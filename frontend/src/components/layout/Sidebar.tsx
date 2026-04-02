"use client";

import { BarChart3, ClipboardList, Star, Upload, Users, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface SidebarLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

const LINKS: SidebarLink[] = [
  { href: "/candidates", label: "Анкеты кандидатов", icon: Users },
  { href: "/dashboard", label: "Рейтинг", icon: BarChart3 },
  { href: "/upload", label: "Загрузка", icon: Upload },
  { href: "/audit", label: "Журнал", icon: ClipboardList },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="hidden lg:flex flex-col w-[220px] min-h-[calc(100vh-4.8rem)] py-6 px-4 border-r"
      style={{ borderColor: "rgba(20, 20, 20, 0.06)" }}
    >
      <div className="eyebrow mb-4 px-3">Навигация</div>
      <nav className="flex flex-col gap-1">
        {LINKS.map((link) => {
          const isActive = pathname === link.href || pathname.startsWith(link.href + "/");
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
