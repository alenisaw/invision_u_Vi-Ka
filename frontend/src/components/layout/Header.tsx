"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import BrandMark from "./BrandMark";
import ThemeToggle from "./ThemeToggle";
import LanguageToggle from "./LanguageToggle";
import UserMenu from "./UserMenu";

export default function Header() {
  const pathname = usePathname();
  const { locale, t } = useLocale();
  const { user } = useAuth();

  const navLinks = [
    { href: "/candidates", label: t("nav.candidates") },
    { href: "/dashboard", label: t("nav.dashboard") },
    { href: "/upload", label: t("nav.upload") },
    ...(user?.role === "admin" ? [{ href: "/admin/users", label: t("nav.users") }] : []),
    ...(user?.role === "admin"
      ? [{ href: "/admin/metrics", label: locale === "ru" ? "Метрики" : "Metrics" }]
      : []),
    ...(user?.role === "admin" ? [{ href: "/audit", label: t("nav.audit") }] : []),
  ];

  return (
    <header
      className="sticky top-0 z-[60] min-h-[5.4rem] flex items-center px-5 lg:px-8 border-b"
      style={{
        backdropFilter: "blur(18px)",
        background: "var(--surface-soft)",
        borderColor: "var(--brand-line)",
      }}
    >
      <div className="flex items-center mr-6 lg:mr-12 min-w-0">
        <BrandMark />
      </div>

      <nav className="hidden md:flex items-center gap-6 lg:gap-8 min-w-0 mr-auto">
        {navLinks.map((link) => {
          const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`group relative text-[0.94rem] font-[700] transition-colors duration-200 ${
                isActive ? "" : "hover:text-[var(--brand-ink)]"
              }`}
              style={{
                color: isActive ? "var(--brand-ink)" : "var(--brand-muted-strong)",
              }}
            >
              {link.label}
              <span
                className={`absolute -bottom-1 left-0 h-[2px] transition-all duration-[350ms] ease-in-out origin-left ${
                  isActive ? "scale-x-100 opacity-100" : "scale-x-[0.32] opacity-30 group-hover:scale-x-100 group-hover:opacity-100"
                }`}
                style={{
                  background: "var(--brand-lime)",
                  width: "100%",
                }}
              />
            </Link>
          );
        })}
      </nav>

      <div className="ml-auto flex items-center gap-3 lg:gap-4">
        <UserMenu />
        <ThemeToggle />
        <LanguageToggle />
      </div>
    </header>
  );
}
