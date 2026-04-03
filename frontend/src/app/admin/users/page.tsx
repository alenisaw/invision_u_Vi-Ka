"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import { adminApi, ApiError } from "@/lib/api";
import { getRoleLabel, getUserInitials } from "@/lib/auth-ui";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import { formatDateTime } from "@/lib/i18n";
import type { AdminUser, UserRole } from "@/types";

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
  const { locale } = useLocale();
  const { user, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
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
    () =>
      locale === "ru"
        ? {
            title: "Пользователи и доступ",
            description:
              "Управление закрытым контуром комиссии: роли, доступы и быстрые demo-учетки.",
            createTitle: "Создать аккаунт",
            createDescription:
              "Администратор вручную выдает доступ. Публичной регистрации нет.",
            listTitle: "Текущие аккаунты",
            listDescription: "Изменяйте роль, активность и пароль прямо на карточке пользователя.",
            email: "Email",
            fullName: "Имя",
            password: "Пароль",
            active: "Активен",
            createdAt: "Создан",
            lastLogin: "Последний вход",
            save: "Сохранить",
            create: "Создать",
            loading: "Загружаю пользователей...",
            empty: "Пока нет пользователей",
            noLogin: "Еще не входил",
            accessPack: "Стартовый набор доступа",
            accessPackDescription:
              "Эти аккаунты поднимаются автоматически и подходят для проверки ролей.",
            accounts: "аккаунтов",
            activeCount: "активных",
            role: "Роль",
          }
        : {
            title: "Users and Access",
            description:
              "Manage the closed committee workspace: roles, access, and demo seed accounts.",
            createTitle: "Create account",
            createDescription:
              "Access is provisioned manually by an admin. There is no public sign-up.",
            listTitle: "Current accounts",
            listDescription: "Update role, active state, and password directly on each card.",
            email: "Email",
            fullName: "Name",
            password: "Password",
            active: "Active",
            createdAt: "Created",
            lastLogin: "Last login",
            save: "Save",
            create: "Create",
            loading: "Loading users...",
            empty: "No users yet",
            noLogin: "Never signed in",
            accessPack: "Default access pack",
            accessPackDescription:
              "These accounts are seeded automatically and cover each access level.",
            accounts: "accounts",
            activeCount: "active",
            role: "Role",
          },
    [locale],
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
      const nextUsers = await adminApi.listUsers();
      setUsers(nextUsers);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to load users");
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
      setError(nextError instanceof Error ? nextError.message : "Failed to create user");
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
      if (nextError instanceof ApiError) {
        setError(nextError.message);
      } else {
        setError("Failed to update user");
      }
    } finally {
      setSavingId(null);
    }
  }

  const activeUsers = users.filter((item) => item.is_active).length;

  return (
    <>
      <Header />
      <main className="min-w-0 p-6 lg:p-10 pb-24">
        <div className="container-app">
            <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[800] mb-2 tracking-tighter">
              {labels.title}
            </h1>
            <p className="text-[1rem] mb-8 text-muted">{labels.description}</p>

            {error && (
              <div className="card p-4 mb-8 border border-[var(--brand-coral)]/20 bg-[var(--brand-coral)]/8 text-[var(--brand-coral)] font-[700]">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
              <StatChip
                label={labels.accounts}
                value={String(users.length)}
              />
              <StatChip
                label={labels.activeCount}
                value={String(activeUsers)}
              />
              <StatChip
                label={getRoleLabel("chair", locale)}
                value={String(users.filter((item) => item.role === "chair").length)}
              />
              <StatChip
                label={getRoleLabel("reviewer", locale)}
                value={String(users.filter((item) => item.role === "reviewer").length)}
              />
            </div>

            <div className="card p-6 mb-8">
              <div className="flex flex-col gap-2 mb-5">
                <div className="eyebrow">{labels.accessPack}</div>
                <p className="text-[0.95rem] text-muted max-w-[56rem]">{labels.accessPackDescription}</p>
              </div>
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
                <div className="eyebrow mb-3">{labels.createTitle}</div>
                <p className="text-[0.94rem] text-muted mb-6">{labels.createDescription}</p>
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
                    onChange={(event) =>
                      setForm((current) => ({ ...current, role: event.target.value as UserRole }))
                    }
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
                      onChange={(event) =>
                        setForm((current) => ({ ...current, is_active: event.target.checked }))
                      }
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
                <div className="eyebrow mb-3">{labels.listTitle}</div>
                <p className="text-[0.94rem] text-muted mb-6">{labels.listDescription}</p>
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
            onChange={(event) =>
              setDraft((current) => ({ ...current, is_active: event.target.checked }))
            }
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
        className="btn mt-5 w-full py-3 text-[0.9rem] font-[900]"
      >
        {labels.save}
      </button>
    </div>
  );
}

function StatChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.3rem] px-5 py-5 bg-[var(--surface-soft)] border" style={{ borderColor: "var(--brand-line)" }}>
      <div className="text-[0.74rem] font-[800] uppercase tracking-[0.12em] text-muted mb-2">
        {label}
      </div>
      <div className="text-[1.55rem] font-[900]">{value}</div>
    </div>
  );
}

function FieldLabel({ label }: { label: string }) {
  return <div className="text-[0.8rem] font-[800] uppercase tracking-[0.12em] text-muted">{label}</div>;
}
