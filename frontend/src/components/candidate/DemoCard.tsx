"use client";

import { useLocale } from "@/components/providers/LocaleProvider";
import { localizeProgramName } from "@/lib/i18n";
import type { FixtureMeta } from "@/types";

interface DemoCardProps {
  meta: FixtureMeta;
  onRun: (slug: string) => void;
  viewMode?: "grid" | "list";
  isRunning: boolean;
  isDisabled: boolean;
  actionLabel?: string;
}

export default function DemoCard({
  meta,
  onRun,
  viewMode = "grid",
  isRunning,
  isDisabled,
  actionLabel,
}: DemoCardProps) {
  const { locale, t } = useLocale();
  const isList = viewMode === "list";

  return (
    <div
      className={`card p-6 transition-all duration-300 w-full h-full flex ${
        isDisabled ? "opacity-40 grayscale pointer-events-none" : ""
      } ${isList ? "flex-row items-center gap-6" : "flex-col"}`}
    >
      <div className="flex-1 min-w-0 flex flex-col h-full">
        <div className="flex items-start gap-3 mb-4 w-full">
          <span
            className="px-2.5 py-1 rounded-[0.6rem] text-[0.65rem] font-[800] uppercase tracking-widest shrink-0 mt-0.5"
            style={{ background: "var(--surface-subtle-2)", color: "var(--brand-ink)" }}
          >
            {meta.language.toUpperCase()}
          </span>
          <span
            className="text-[0.75rem] font-[800] text-muted uppercase tracking-wider leading-snug line-clamp-2"
            title={localizeProgramName(meta.program, locale)}
          >
            {localizeProgramName(meta.program, locale)}
          </span>
        </div>

        <h3 className={`${isList ? "text-[1.1rem]" : "text-[1.25rem]"} font-[900] leading-tight mb-3 tracking-tight`}>
          {meta.display_name}
        </h3>

        <p className={`text-[0.88rem] font-[500] italic text-muted leading-relaxed ${!isList ? "line-clamp-3 min-h-[4rem]" : "truncate"}`}>
          &ldquo;{meta.content_preview}&rdquo;
        </p>
      </div>

      <div className={`${isList ? "w-[220px] pt-0 border-t-0" : "pt-5 mt-auto border-t border-[var(--brand-line)]"}`}>
        <button
          onClick={() => onRun(meta.slug)}
          disabled={isRunning || isDisabled}
          className={`btn btn--sm w-full font-[800] tracking-wide transition-all ${
            isRunning
              ? "bg-[var(--surface-subtle-2)] text-muted cursor-wait"
              : "btn--dark"
          }`}
        >
          {isRunning ? t("upload.demo.running") : actionLabel ?? t("upload.demo.run")}
        </button>
      </div>
    </div>
  );
}
