"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale } from "@/components/providers/LocaleProvider";
import ThemeToggle from "./ThemeToggle";
import LanguageToggle from "./LanguageToggle";

export default function Header() {
  const pathname = usePathname();
  const { t } = useLocale();

  const navLinks = [
    { href: "/candidates", label: t("nav.candidates") },
    { href: "/dashboard", label: t("nav.dashboard") },
    { href: "/upload", label: t("nav.upload") },
    { href: "/audit", label: t("nav.audit") },
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
      <div className="flex items-center gap-4 mr-6 lg:mr-12 min-w-0">
        <div
          className="w-11 h-11 rounded-full shrink-0 flex items-center justify-center font-[900] text-[0.95rem]"
          style={{
            background: "var(--brand-lime)",
            color: "#101311",
            boxShadow: "0 0 0 6px color-mix(in srgb, var(--brand-lime) 16%, transparent)",
          }}
        >
          U
        </div>
        <div className="min-w-0">
          <div
            className="font-[900] text-[1.02rem] whitespace-nowrap leading-none"
            style={{ letterSpacing: "-0.04em", color: "var(--brand-ink)" }}
          >
            inVision U
          </div>
        </div>
      </div>

      <nav className="hidden md:flex items-center gap-6 lg:gap-8 min-w-0">
        {navLinks.map((link) => {
          const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
          return (
            <Link
              key={link.href}
              href={link.href}
              className="relative text-[0.94rem] font-[700] transition-colors"
              style={{
                color: isActive ? "var(--brand-ink)" : "var(--brand-muted-strong)",
              }}
            >
              {link.label}
              <span
                className="absolute -bottom-1 left-0 w-full h-[2px] transition-transform duration-[350ms] ease-in-out origin-left"
                style={{
                  background: "var(--brand-lime)",
                  transform: isActive ? "scaleX(1)" : "scaleX(0)",
                }}
              />
            </Link>
          );
        })}
      </nav>

      <div className="ml-auto flex items-center gap-3 lg:gap-4">
        <LanguageToggle />
        <ThemeToggle />
        <div className="hidden xl:flex items-center gap-3">
          <span className="text-[0.8rem] font-[700] text-muted whitespace-nowrap">
            {t("brand.title")}
          </span>
          <a
            href="https://youtu.be/dQw4w9WgXcQ"
            target="_blank"
            rel="noreferrer"
            title={t("header.rickroll")}
            className="w-9 h-9 rounded-full flex items-center justify-center text-[0.8rem] font-[900]"
            style={{
              background: "var(--brand-ink)",
              color: "var(--brand-paper)",
            }}
          >
            {t("brand.badge")}
          </a>
        </div>
      </div>
    </header>
  );
}
