"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import BrandMark from "@/components/layout/BrandMark";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import { getRoleLabel } from "@/lib/auth-ui";
import type { UserRole } from "@/types";

const QUICK_ACCOUNTS: Array<{
  email: string;
  password: string;
  name: string;
  role: UserRole;
}> = [
  { email: "admin@invisionu.local", password: "admin", name: "Main Admin", role: "admin" },
  { email: "ops.admin@invisionu.local", password: "111111", name: "Aruzhan Admin", role: "admin" },
  { email: "chair@invisionu.local", password: "222222", name: "Dana Chair", role: "chair" },
  { email: "reviewer@invisionu.local", password: "333333", name: "Miras Reviewer", role: "reviewer" },
];

export default function LoginPage() {
  const router = useRouter();
  const { locale, t } = useLocale();
  const { user, loading, login } = useAuth();
  const [email, setEmail] = useState("admin@invisionu.local");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState("");
  const labels = useMemo(
    () => ({
      eyebrow: t("login.eyebrow"),
      title: t("login.title"),
      description: t("login.description"),
      email: t("login.email"),
      password: t("login.password"),
      submit: t("login.submit"),
      quickTitle: t("login.quickTitle"),
      quickDescription: t("login.quickDescription"),
      accessEyebrow: t("login.accessEyebrow"),
    }),
    [t],
  );

  useEffect(() => {
    if (!loading && user) {
      router.replace(user.role === "admin" ? "/admin/users" : "/candidates");
    }
  }, [loading, router, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    try {
      await login(email, password);
    } catch (nextError) {
      setError(nextError instanceof ApiError ? nextError.message : t("login.error"));
    }
  }

  return (
    <main className="min-h-screen bg-[var(--surface-base)] px-6 py-8 lg:px-10">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl grid-cols-1 gap-6 lg:grid-cols-[1.08fr_0.92fr]">
        <section
          className="relative overflow-hidden rounded-[2.5rem] border p-8 lg:p-12"
          style={{
            borderColor: "var(--brand-line)",
            background:
              "radial-gradient(circle at top left, color-mix(in srgb, var(--brand-blue) 20%, transparent) 0, transparent 42%), radial-gradient(circle at bottom right, color-mix(in srgb, var(--brand-lime) 18%, transparent) 0, transparent 36%), var(--surface-soft)",
          }}
        >
          <div className="mb-8">
            <BrandMark size="lg" />
          </div>

          <div className="max-w-[36rem]">
            <div className="eyebrow mb-4">{labels.eyebrow}</div>
            <h1 className="text-[clamp(2.8rem,2.1rem+2vw,5rem)] font-[900] tracking-[-0.08em] leading-[0.94] mb-5">
              {labels.title}
            </h1>
            <p className="text-[1.02rem] leading-relaxed text-muted max-w-[34rem]">
              {labels.description}
            </p>
          </div>

          <div className="mt-12">
            <div className="eyebrow mb-4">{labels.quickTitle}</div>
            <p className="text-[0.94rem] text-muted mb-5 max-w-[32rem]">
              {labels.quickDescription}
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {QUICK_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  onClick={() => {
                    setEmail(account.email);
                    setPassword(account.password);
                    setError("");
                  }}
                  className="rounded-[1.5rem] border p-4 text-left transition-all duration-200 hover:-translate-y-[2px]"
                  style={{
                    borderColor: "var(--brand-line)",
                    background: "color-mix(in srgb, var(--surface-subtle) 84%, transparent)",
                  }}
                >
                  <div className="text-[0.98rem] font-[800] mb-1">{account.name}</div>
                  <div className="text-[0.78rem] font-[700] text-muted mb-3">
                    {getRoleLabel(account.role, locale)}
                  </div>
                  <div className="text-[0.82rem] font-[600] text-muted">{account.email}</div>
                  <div className="text-[0.82rem] font-[800] mt-2" style={{ color: "var(--brand-blue)" }}>
                    {account.password}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-[2.5rem] border p-8 lg:p-10 bg-[var(--surface-soft)]" style={{ borderColor: "var(--brand-line)" }}>
          <div className="mb-8">
            <div className="eyebrow mb-4">{labels.accessEyebrow}</div>
            <h2 className="text-[clamp(2rem,1.7rem+1vw,3rem)] font-[900] tracking-[-0.06em] mb-3">
              {labels.submit}
            </h2>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="block text-[0.82rem] font-[800] uppercase tracking-[0.12em] mb-2 text-muted">
                {labels.email}
              </span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-[1.15rem] px-4 py-3.5"
                autoComplete="email"
                required
              />
            </label>

            <label className="block">
              <span className="block text-[0.82rem] font-[800] uppercase tracking-[0.12em] mb-2 text-muted">
                {labels.password}
              </span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-[1.15rem] px-4 py-3.5"
                autoComplete="current-password"
                required
              />
            </label>

            {error && (
              <div className="rounded-[1.15rem] border px-4 py-3 text-[0.92rem] font-[700] text-[var(--brand-coral)] border-[var(--brand-coral)]/20 bg-[var(--brand-coral)]/8">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn w-full py-3.5 text-[0.95rem] font-[900]"
            >
              {labels.submit}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
