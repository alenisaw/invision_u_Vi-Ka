"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import PipelineMetricsPanel from "@/components/admin/PipelineMetricsPanel";
import Header from "@/components/layout/Header";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import { getRoleLabel, getUserInitials } from "@/lib/auth-ui";
import { adminApi, ApiError } from "@/lib/api";
import { formatDateTime } from "@/lib/i18n";
import type { AdminUser, PipelineMetrics, UserRole } from "@/types";

const ROLE_OPTIONS: UserRole[] = ["admin", "chair", "reviewer"];

const DEFAULT_ACCESS_PACK: Array<{
  email: string;
  password: string;
  role: UserRole;
}> = [
  { email: "admin@invisionu.local", password: "admin", role: "admin" },
  { email: "ops.admin@invisionu.local", password: "111111", role: "admin" },
  { email: "chair@invisionu.local", password: "222222", role: "chair" },
  { email: "reviewer@invisionu.local", password: "333333", role: "reviewer" },
];

export default function AdminUsersPage() {
  const router = useRouter();
  const { locale, t } = useLocale();
  const { user, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [pipelineMetrics, setPipelineMetrics] = useState<PipelineMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    password: "",
    role: "reviewer" as UserRole,
    is_active: true,
  });

  const labels = useMemo(
    () => ({
      title: t("adminUsers.title"),
      createTitle: t("adminUsers.createTitle"),
      listTitle: t("adminUsers.listTitle"),
      email: t("adminUsers.email"),
      fullName: t("adminUsers.fullName"),
      password: t("adminUsers.password"),
      active: t("adminUsers.active"),
      createdAt: t("adminUsers.createdAt"),
      lastLogin: t("adminUsers.lastLogin"),
      create: t("adminUsers.create"),
      loading: t("adminUsers.loading"),
      empty: t("adminUsers.empty"),
      noLogin: t("adminUsers.noLogin"),
      accessPack: t("adminUsers.accessPack"),
      accounts: t("adminUsers.accounts"),
      activeCount: t("adminUsers.activeCount"),
      role: t("adminUsers.role"),
    }),
    [t],
  );

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.replace("/login");
    }
  }, [authLoading, router, user]);

  useEffect(() => {
    if (user?.role === "admin") {
      void loadUsers();
    }
  }, [user?.role]);

  async function loadUsers() {
    setLoading(true);
    setError("");
    try {
      const [nextUsers, nextMetrics] = await Promise.all([
        adminApi.listUsers(),
        adminApi.getPipelineMetrics(16),
      ]);
      setUsers(nextUsers);
      setPipelineMetrics(nextMetrics);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : t("adminUsers.loadError"));
    } finally {
      setLoading(false);
    }
  }

  async function createUser() {
    setCreating(true);
    setError("");
    try {
      const created = await adminApi.createUser(form);
      setUsers((current) => [...current, created]);
      setForm({
        email: "",
        full_name: "",
        password: "",
        role: "reviewer",
        is_active: true,
      });
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : t("adminUsers.createError"));
    } finally {
      setCreating(false);
    }
  }

  async function updateUser(nextUser: AdminUser, password = "") {
    setSavingId(nextUser.id);
    setError("");
    try {
      const updated = await adminApi.updateUser(nextUser.id, {
        full_name: nextUser.full_name,
        role: nextUser.role,
        is_active: nextUser.is_active,
        ...(password ? { password } : {}),
      });
      setUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (nextError) {
      setError(nextError instanceof ApiError ? nextError.message : t("adminUsers.updateError"));
    } finally {
      setSavingId(null);
    }
  }

  const activeUsers = users.filter((item) => item.is_active).length;

  return (
    <>
      <Header />
      <main className="min-w-0 px-5 py-6 lg:px-8 lg:py-8 pb-24">
        <div className="container-app page-shell">
          <div className="page-stack">
            <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[800] tracking-tighter">
              {labels.title}
            </h1>

            {error ? (
              <div className="card p-4 border border-[var(--brand-coral)]/20 bg-[var(--brand-coral)]/8 text-[var(--brand-coral)] font-[700]">
                {error}
              </div>
            ) : null}

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatChip label={labels.accounts} value={String(users.length)} />
              <StatChip label={labels.activeCount} value={String(activeUsers)} />
              <StatChip label={getRoleLabel("chair", locale)} value={String(users.filter((item) => item.role === "chair").length)} />
              <StatChip label={getRoleLabel("reviewer", locale)} value={String(users.filter((item) => item.role === "reviewer").length)} />
            </div>

            <div className="card p-6">
              {pipelineMetrics ? (
                <PipelineMetricsPanel
                  metrics={pipelineMetrics}
                  locale={locale}
                  mode="compact"
                  showReportLink
                />
              ) : (
                <div className="py-6 text-center text-muted font-[700]">{labels.loading}</div>
              )}
            </div>

            <div className="card p-6">
              <div className="mb-5 text-[1rem] font-[800]">{labels.accessPack}</div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {DEFAULT_ACCESS_PACK.map((account) => (
                  <div
                    key={account.email}
                    className="rounded-[1.35rem] border p-4"
                    style={{ borderColor: "var(--brand-line)", background: "var(--surface-subtle)" }}
                  >
                    <div className="text-[0.96rem] font-[800] mb-1">{account.email}</div>
                    <div className="text-[0.8rem] font-[700] text-muted mb-2">
                      {getRoleLabel(account.role, locale)}
                    </div>
                    <div className="text-[0.84rem] font-[800]" style={{ color: "var(--brand-blue)" }}>
                      {account.password}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[420px_minmax(0,1fr)] gap-6">
              <section className="card p-6">
                <div className="mb-6 text-[1rem] font-[800]">{labels.createTitle}</div>
                <div className="space-y-4">
                  <FieldLabel label={labels.email} />
                  <input
                    value={form.email}
                    onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                    placeholder="name@invisionu.local"
                    className="w-full rounded-[1rem] px-4 py-3"
                  />
                  <FieldLabel label={labels.fullName} />
                  <input
                    value={form.full_name}
                    onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
                    placeholder="Ainur Sadykova"
                    className="w-full rounded-[1rem] px-4 py-3"
                  />
                  <FieldLabel label={labels.password} />
                  <input
                    type="password"
                    value={form.password}
                    onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                    placeholder="111111"
                    className="w-full rounded-[1rem] px-4 py-3"
                  />
                  <FieldLabel label={labels.role} />
                  <select
                    value={form.role}
                    onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as UserRole }))}
                    className="w-full rounded-[1rem] px-4 py-3"
                  >
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role} value={role}>
                        {getRoleLabel(role, locale)}
                      </option>
                    ))}
                  </select>
                  <label className="flex items-center gap-3 text-[0.92rem] font-[700]">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                    />
                    {labels.active}
                  </label>
                  <button
                    onClick={() => void createUser()}
                    disabled={creating}
                    className="btn w-full py-3 text-[0.95rem] font-[900]"
                  >
                    {labels.create}
                  </button>
                </div>
              </section>

              <section className="card p-6">
                <div className="mb-6 text-[1rem] font-[800]">{labels.listTitle}</div>
                {loading ? (
                  <div className="py-12 text-center text-muted font-[700]">{labels.loading}</div>
                ) : users.length === 0 ? (
                  <div className="py-12 text-center text-muted font-[700]">{labels.empty}</div>
                ) : (
                  <div className="grid grid-cols-1 2xl:grid-cols-2 gap-4">
                    {users.map((item) => (
                      <AdminUserCard
                        key={item.id}
                        item={item}
                        locale={locale}
                        labels={labels}
                        saving={savingId === item.id}
                        onSave={updateUser}
                      />
                    ))}
                  </div>
                )}
              </section>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}

function AdminUserCard({
  item,
  locale,
  labels,
  saving,
  onSave,
}: {
  item: AdminUser;
  locale: "ru" | "en";
  labels: Record<string, string>;
  saving: boolean;
  onSave: (user: AdminUser, password?: string) => Promise<void>;
}) {
  const [draft, setDraft] = useState(item);
  const [password, setPassword] = useState("");

  useEffect(() => {
    setDraft(item);
  }, [item]);

  return (
    <div
      className="rounded-[1.45rem] border p-5"
      style={{ borderColor: "var(--brand-line)", background: "var(--surface-subtle)" }}
    >
      <div className="flex items-start gap-4 mb-5">
        <div
          className="flex h-12 w-12 items-center justify-center rounded-full text-[0.9rem] font-[900]"
          style={{
            background: "linear-gradient(135deg, var(--brand-lime) 0%, var(--brand-blue) 100%)",
            color: "#101311",
          }}
        >
          {getUserInitials(draft.full_name)}
        </div>
        <div className="min-w-0">
          <div className="text-[1rem] font-[900] truncate">{draft.full_name}</div>
          <div className="text-[0.82rem] font-[600] text-muted truncate">{draft.email}</div>
          <div className="text-[0.78rem] font-[800] mt-2" style={{ color: "var(--brand-blue)" }}>
            {getRoleLabel(draft.role, locale)}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <input
          value={draft.full_name}
          onChange={(event) => setDraft((current) => ({ ...current, full_name: event.target.value }))}
          className="w-full rounded-[1rem] px-4 py-3"
          aria-label={labels.fullName}
        />
        <select
          value={draft.role}
          onChange={(event) => setDraft((current) => ({ ...current, role: event.target.value as UserRole }))}
          className="w-full rounded-[1rem] px-4 py-3"
        >
          {ROLE_OPTIONS.map((role) => (
            <option key={role} value={role}>
              {getRoleLabel(role, locale)}
            </option>
          ))}
        </select>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full rounded-[1rem] px-4 py-3"
          placeholder={labels.password}
        />
        <label className="flex items-center gap-3 text-[0.9rem] font-[700]">
          <input
            type="checkbox"
            checked={draft.is_active}
            onChange={(event) => setDraft((current) => ({ ...current, is_active: event.target.checked }))}
          />
          {labels.active}
        </label>
      </div>

      <div className="mt-5 text-[0.8rem] text-muted space-y-1">
        <div>
          <span className="font-[800] text-[var(--brand-ink)]">{labels.createdAt}: </span>
          {formatDateTime(draft.created_at, locale)}
        </div>
        <div>
          <span className="font-[800] text-[var(--brand-ink)]">{labels.lastLogin}: </span>
          {draft.last_login_at ? formatDateTime(draft.last_login_at, locale) : labels.noLogin}
        </div>
      </div>

      <button
        onClick={() => void onSave(draft, password)}
        disabled={saving}
        className="btn w-full mt-5 py-3 text-[0.92rem] font-[900]"
      >
        {saving ? "..." : tSafe(locale, "save")}
      </button>
    </div>
  );
}

function StatChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.15rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-5 py-5">
      <div className="mb-2 text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
        {label}
      </div>
      <div className="text-[1.6rem] font-[900]">{value}</div>
    </div>
  );
}

function FieldLabel({ label }: { label: string }) {
  return (
    <div className="text-[0.78rem] font-[800] uppercase tracking-[0.12em] text-muted">
      {label}
    </div>
  );
}

function tSafe(locale: "ru" | "en", key: "save") {
  if (key === "save") {
    return locale === "ru" ? "Сохранить" : "Save";
  }
  return key;
}
