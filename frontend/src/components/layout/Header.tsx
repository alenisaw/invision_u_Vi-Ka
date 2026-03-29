"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/dashboard", label: "Рейтинг" },
  { href: "/shortlist", label: "Шорт-лист" },
  { href: "/upload", label: "Загрузка" },
  { href: "/audit", label: "Журнал" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header
      className="sticky top-0 z-[60] min-h-[4.8rem] flex items-center px-8 border-b"
      style={{
        backdropFilter: "blur(18px)",
        background: "rgba(255, 255, 255, 0.78)",
        borderColor: "rgba(20, 20, 20, 0.06)",
      }}
    >
      <div className="flex items-center gap-3 mr-12">
        <div
          className="w-4 h-4 rounded-full"
          style={{
            background: "linear-gradient(135deg, var(--brand-lime), var(--brand-blue))",
            boxShadow: "0 0 0 5px rgba(193, 241, 29, 0.18)",
          }}
        />
        <span className="font-[800] text-[1.05rem] whitespace-nowrap" style={{ letterSpacing: "-0.03em" }}>
          inVision U
        </span>
      </div>

      <nav className="flex items-center gap-8">
        {NAV_LINKS.map((link) => {
          const isActive = pathname === link.href || pathname.startsWith(link.href + "/");
          return (
            <Link
              key={link.href}
              href={link.href}
              className="relative text-[0.98rem] font-[700] transition-colors"
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

      <div className="ml-auto flex items-center gap-4">
        <span className="text-[0.82rem] font-[700]" style={{ color: "var(--brand-muted)" }}>
          Приёмная комиссия
        </span>
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center text-[0.82rem] font-[800]"
          style={{ background: "var(--brand-ink)", color: "var(--brand-paper)" }}
        >
          AC
        </div>
      </div>
    </header>
  );
}
