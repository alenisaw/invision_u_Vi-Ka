"use client";

import { BarChart3, ClipboardList, Upload, Users, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale } from "@/components/providers/LocaleProvider";

interface SidebarLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

export default function Sidebar() {
  const pathname = usePathname();
  const { t } = useLocale();

  const links: SidebarLink[] = [
    { href: "/candidates", label: t("nav.candidates"), icon: Users },
    { href: "/dashboard", label: t("nav.dashboard"), icon: BarChart3 },
    { href: "/upload", label: t("nav.upload"), icon: Upload },
    { href: "/audit", label: t("nav.audit"), icon: ClipboardList },
  ];

  return (
    <aside
      className="hidden lg:flex flex-col w-[232px] min-h-[calc(100vh-5.4rem)] py-6 px-4 border-r"
      style={{ borderColor: "rgba(20, 20, 20, 0.06)" }}
    >
      <div className="eyebrow mb-4 px-3">{t("nav.label")}</div>
      <nav className="flex flex-col gap-1">
        {links.map((link) => {
          const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-[1rem] text-[0.92rem] font-[600] transition-colors duration-200"
              style={{
                background: isActive ? "rgba(193, 241, 29, 0.18)" : "transparent",
                color: isActive ? "var(--brand-ink)" : "var(--brand-muted-strong)",
              }}
            >
              <Icon aria-hidden="true" className="h-[1.15rem] w-[1.15rem] shrink-0" strokeWidth={2.1} />
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
