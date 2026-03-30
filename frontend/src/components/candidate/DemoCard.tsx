"use client";

import type { FixtureMeta } from "@/types";

const ARCHETYPE_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  strong:     { bg: "rgba(193, 241, 29, 0.18)", color: "#415005", label: "Сильный" },
  balanced:   { bg: "rgba(61, 237, 241, 0.16)", color: "#0a6a6d", label: "Средний" },
  weak:       { bg: "rgba(255, 142, 112, 0.14)", color: "#ac472e", label: "Слабый" },
  risky:      { bg: "rgba(255, 200, 60, 0.18)", color: "#7a5d00",  label: "Риск" },
  incomplete: { bg: "rgba(20, 20, 20, 0.06)",   color: "var(--brand-muted)", label: "Неполный" },
};

interface DemoCardProps {
  meta: FixtureMeta;
  onRun: (slug: string) => void;
  onToggleSelect: (slug: string) => void;
  isRunning: boolean;
  isSelected: boolean;
  isDisabled: boolean;
}

export default function DemoCard({
  meta,
  onRun,
  onToggleSelect,
  isRunning,
  isSelected,
  isDisabled,
}: DemoCardProps) {
  const style = ARCHETYPE_STYLES[meta.archetype] ?? ARCHETYPE_STYLES.balanced;

  return (
    <div
      className="card p-5 flex flex-col gap-3 transition-shadow duration-200"
      style={{
        outline: isSelected ? "2px solid var(--brand-blue)" : "none",
        outlineOffset: "-2px",
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="text-[1rem] font-[700] truncate">{meta.display_name}</h3>
          <p className="text-[0.82rem] font-[600] truncate" style={{ color: "var(--brand-muted)" }}>
            {meta.program}
          </p>
        </div>
        <span
          className="shrink-0 px-2.5 py-1 rounded-full text-[0.72rem] font-[800] uppercase tracking-[0.06em]"
          style={{ background: style.bg, color: style.color }}
        >
          {style.label}
        </span>
      </div>

      <p
        className="text-[0.84rem] font-[500] line-clamp-3"
        style={{ color: "var(--brand-muted-strong)" }}
      >
        {meta.description}
      </p>

      <div className="flex items-center gap-2 text-[0.76rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
        <span
          className="px-2 py-0.5 rounded-full"
          style={{ background: "rgba(20, 20, 20, 0.05)" }}
        >
          {meta.language.toUpperCase()}
        </span>
        <span
          className="px-2 py-0.5 rounded-full"
          style={{ background: "rgba(20, 20, 20, 0.05)" }}
        >
          {meta.expected_outcome.replace(/_/g, " ")}
        </span>
      </div>

      <div className="flex items-center gap-2 mt-auto pt-2">
        <button
          onClick={() => onRun(meta.slug)}
          disabled={isRunning || isDisabled}
          className="btn btn--dark btn--sm flex-1"
          style={{
            opacity: isRunning || isDisabled ? 0.4 : 1,
            cursor: isRunning || isDisabled ? "not-allowed" : "pointer",
          }}
        >
          {isRunning ? "Обработка..." : "Запустить пайплайн"}
        </button>
        <label
          className="flex items-center gap-1.5 cursor-pointer text-[0.78rem] font-[600] shrink-0"
          style={{ color: "var(--brand-muted)" }}
        >
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect(meta.slug)}
            className="accent-[#3dedf1] w-4 h-4"
          />
          Сравнить
        </label>
      </div>
    </div>
  );
}
