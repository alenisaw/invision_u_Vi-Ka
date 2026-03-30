"use client";

import type { FixtureMeta } from "@/types";

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
  return (
    <div
      className="card p-5 flex flex-col gap-3 transition-shadow duration-200"
      style={{
        outline: isSelected ? "2px solid var(--brand-blue)" : "none",
        outlineOffset: "-2px",
      }}
    >
      <div className="flex-1 min-w-0">
        <h3 className="text-[1rem] font-[700] truncate">{meta.display_name}</h3>
        <p className="text-[0.82rem] font-[600] truncate" style={{ color: "var(--brand-muted)" }}>
          {meta.program}
        </p>
      </div>

      <p
        className="text-[0.84rem] font-[500] line-clamp-3 italic"
        style={{ color: "var(--brand-muted-strong)" }}
      >
        {meta.essay_preview}
      </p>

      <div className="flex items-center gap-2 text-[0.76rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
        <span
          className="px-2 py-0.5 rounded-full"
          style={{ background: "rgba(20, 20, 20, 0.05)" }}
        >
          {meta.language.toUpperCase()}
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
