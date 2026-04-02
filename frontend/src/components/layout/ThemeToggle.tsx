"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useLocale } from "@/components/providers/LocaleProvider";

export default function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const { t } = useLocale();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const buttonStyle: React.CSSProperties = {
    borderColor: "var(--brand-line)",
    background: "var(--surface-soft)",
    color: "var(--brand-ink)",
    boxShadow: "var(--surface-shadow)",
  };

  if (!mounted) {
    return (
      <button
        type="button"
        aria-label={t("theme.toggle")}
        className="w-10 h-10 rounded-full border flex items-center justify-center"
        style={buttonStyle}
      >
        <Sun className="h-4 w-4" />
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      aria-label={t("theme.toggle")}
      title={isDark ? t("theme.light") : t("theme.dark")}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-200 hover:-translate-y-[1px]"
      style={buttonStyle}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}
