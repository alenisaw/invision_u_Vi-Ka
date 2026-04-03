"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import { getRoleLabel, getUserInitials } from "@/lib/auth-ui";

export default function UserMenu() {
  const router = useRouter();
  const { locale } = useLocale();
  const { user, logout, loading } = useAuth();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  const labels = useMemo(
    () =>
      locale === "ru"
        ? {
            login: "Войти",
            logout: "Выйти из аккаунта",
          }
        : {
            login: "Sign in",
            logout: "Sign out",
          },
    [locale],
  );

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  if (loading) {
    return (
      <div
        className="h-11 min-w-[11rem] rounded-full border"
        style={{ borderColor: "var(--brand-line)", background: "var(--surface-soft)" }}
      />
    );
  }

  if (!user) {
    return (
      <Link
        href="/login"
        className="inline-flex items-center rounded-full border px-4 py-2.5 text-[0.84rem] font-[800]"
        style={{
          borderColor: "var(--brand-line)",
          background: "var(--surface-soft)",
          color: "var(--brand-ink)",
        }}
      >
        {labels.login}
      </Link>
    );
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="inline-flex items-center gap-3 rounded-full border px-2 py-2 pr-4 text-left transition-all duration-200 hover:-translate-y-[1px]"
        style={{
          borderColor: "var(--brand-line)",
          background: "var(--surface-soft)",
          color: "var(--brand-ink)",
          boxShadow: "var(--surface-shadow)",
        }}
      >
        <span
          className="flex h-8 w-8 items-center justify-center rounded-full text-[0.8rem] font-[900]"
          style={{
            background: "linear-gradient(135deg, var(--brand-lime) 0%, var(--brand-blue) 100%)",
            color: "#0f1311",
          }}
        >
          {getUserInitials(user.full_name)}
        </span>
        <span className="hidden sm:flex flex-col min-w-0">
          <span className="truncate text-[0.82rem] font-[800] leading-none">{user.full_name}</span>
          <span className="truncate text-[0.72rem] font-[600] text-muted leading-none mt-1">
            {getRoleLabel(user.role, locale)}
          </span>
        </span>
      </button>

      {open && (
        <div
          className="absolute right-0 top-[calc(100%+0.75rem)] w-[18rem] rounded-[1.35rem] border p-2"
          style={{
            borderColor: "var(--brand-line)",
            background: "var(--surface-soft)",
            boxShadow: "0 18px 54px rgba(0,0,0,0.22)",
          }}
        >
          <div className="rounded-[1rem] px-3 py-3 bg-[var(--surface-subtle)]">
            <div className="text-[0.92rem] font-[800]">{user.full_name}</div>
            <div className="text-[0.76rem] font-[600] text-muted mt-1">{user.email}</div>
            <div className="text-[0.76rem] font-[700] mt-2" style={{ color: "var(--brand-blue)" }}>
              {getRoleLabel(user.role, locale)}
            </div>
          </div>
          <button
            type="button"
            onClick={async () => {
              setOpen(false);
              await logout();
              router.push("/login");
            }}
            className="mt-2 w-full rounded-[1rem] px-3 py-3 text-left text-[0.84rem] font-[800] transition-colors"
            style={{
              background: "transparent",
              color: "var(--brand-ink)",
            }}
          >
            {labels.logout}
          </button>
        </div>
      )}
    </div>
  );
}
