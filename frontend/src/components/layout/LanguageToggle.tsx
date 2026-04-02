"use client";

import { getLocaleDisplayName, type Locale } from "@/lib/i18n";
import { useLocale } from "@/components/providers/LocaleProvider";

const LOCALES: Locale[] = ["ru", "en"];

export default function LanguageToggle() {
  const { locale, setLocale, t } = useLocale();

  return (
    <div
      className="inline-flex items-center gap-1.5 rounded-full border p-1"
      style={{
        borderColor: "var(--brand-line)",
        background: "var(--surface-soft)",
        boxShadow: "var(--surface-shadow)",
      }}
      aria-label={t("locale.toggle")}
      title={t("locale.toggle")}
    >
      {LOCALES.map((item) => {
        const active = item === locale;
        return (
          <button
            key={item}
            type="button"
            onClick={() => setLocale(item)}
            className="min-w-[3rem] rounded-full px-3 py-2 text-[0.78rem] font-[800] transition-all duration-200"
            style={{
              background: active ? "var(--brand-ink)" : "transparent",
              color: active ? "var(--brand-paper)" : "var(--brand-ink)",
            }}
          >
            {getLocaleDisplayName(item)}
          </button>
        );
      })}
    </div>
  );
}
