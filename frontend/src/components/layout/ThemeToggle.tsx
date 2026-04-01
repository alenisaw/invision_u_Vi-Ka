"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
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
        aria-label="Переключить тему"
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
      aria-label="Переключить тему"
      title={isDark ? "Светлая тема" : "Тёмная тема"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-200 hover:-translate-y-[1px]"
      style={buttonStyle}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}