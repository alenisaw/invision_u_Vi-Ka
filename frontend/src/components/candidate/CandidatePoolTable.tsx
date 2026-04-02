"use client";

import Link from "next/link";
import {
  formatDate,
  formatPercent,
  localizeLabels,
} from "@/lib/utils";
import type { RecommendationStatus } from "@/types";
import StatusBadge from "@/components/dashboard/StatusBadge";

export interface CandidatePoolTableItem {
  id: string;
  kind: "processed" | "fixture";
  name: string;
  selectedProgram: string;
  sourceLabel: string;
  sourceTone: "lime" | "blue" | "neutral";
  statusLabel: string;
  recommendationStatus?: RecommendationStatus;
  reviewPriorityIndex?: number | null;
  confidence?: number | null;
  tags: string[];
  createdAt?: string | null;
  actionLabel: string;
  href?: string;
  runSlug?: string;
}

interface CandidatePoolTableProps {
  items: CandidatePoolTableItem[];
  highlightedId?: string | null;
  runningSlug?: string | null;
  onRunFixture: (slug: string) => void;
}

const SOURCE_TONE_CLASS: Record<CandidatePoolTableItem["sourceTone"], string> = {
  lime: "badge--lime",
  blue: "badge--blue",
  neutral: "badge--neutral",
};

export default function CandidatePoolTable({
  items,
  highlightedId,
  runningSlug,
  onRunFixture,
}: CandidatePoolTableProps) {
  if (items.length === 0) {
    return (
      <div className="card p-12 text-center">
        <p className="text-[1rem] font-[600] text-muted">
          Ничего не найдено по текущим фильтрам
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden rounded-[1rem]">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[940px]">
          <thead>
            <tr className="text-left" style={{ borderBottom: "1px solid var(--brand-line)" }}>
              <th className="eyebrow px-5 py-4">Кандидат</th>
              <th className="eyebrow px-5 py-4">Программа</th>
              <th className="eyebrow px-5 py-4">Источник</th>
              <th className="eyebrow px-5 py-4">Статус</th>
              <th className="eyebrow px-5 py-4">Метрики</th>
              <th className="eyebrow px-5 py-4">Метки</th>
              <th className="eyebrow px-5 py-4 w-[140px]">Дата</th>
              <th className="eyebrow px-5 py-4 text-right">Действие</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const isHighlighted = highlightedId === item.id;
              const localizedTags = localizeLabels(item.tags.slice(0, 3));
              const isRunning = Boolean(item.runSlug && runningSlug === item.runSlug);

              return (
                <tr
                  key={item.id}
                  className={`transition-colors duration-[250ms] ${isHighlighted ? "bg-[var(--surface-subtle-2)]" : ""}`}
                  style={{ borderBottom: "1px solid var(--brand-line)" }}
                >
                  <td className="px-5 py-[1rem]">
                    <div className="flex flex-col gap-1">
                      <span className="text-[0.96rem] font-[800] leading-tight">
                        {item.name}
                      </span>
                      <span className="text-[0.78rem] font-[700] text-muted uppercase tracking-[0.08em]">
                        {item.kind === "processed" ? "обработан" : "готов к запуску"}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-[1rem]">
                    <span className="text-[0.84rem] text-muted-strong">
                      {item.selectedProgram}
                    </span>
                  </td>
                  <td className="px-5 py-[1rem]">
                    <span className={`badge ${SOURCE_TONE_CLASS[item.sourceTone]}`}>
                      {item.sourceLabel}
                    </span>
                  </td>
                  <td className="px-5 py-[1rem]">
                    {item.recommendationStatus ? (
                      <StatusBadge status={item.recommendationStatus} />
                    ) : (
                      <span className="badge badge--neutral">{item.statusLabel}</span>
                    )}
                  </td>
                  <td className="px-5 py-[1rem]">
                    <div className="flex flex-col gap-1">
                      <span className="text-[0.82rem] font-[700] text-muted">
                        {item.reviewPriorityIndex != null
                          ? `RPI ${formatPercent(item.reviewPriorityIndex)}`
                          : "RPI появится после обработки"}
                      </span>
                      <span className="text-[0.82rem] font-[700] text-muted">
                        {item.confidence != null
                          ? `Уверенность ${formatPercent(item.confidence)}`
                          : "Без расчета уверенности"}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-[1rem]">
                    <div className="flex flex-wrap gap-1.5">
                      {localizedTags.length > 0 ? (
                        localizedTags.map((tag) => (
                          <span
                            key={`${item.id}-${tag}`}
                            className="text-[0.72rem] font-[700] px-2 py-0.5 rounded-full bg-[var(--surface-subtle-2)] text-[var(--brand-muted-strong)]"
                          >
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span className="text-[0.8rem] text-muted">—</span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-[1rem] whitespace-nowrap">
                    <span className="text-[0.82rem] text-muted font-numbers">
                      {item.createdAt ? formatDate(item.createdAt) : "—"}
                    </span>
                  </td>
                  <td className="px-5 py-[1rem] text-right">
                    {item.href ? (
                      <Link href={item.href} className="btn btn--sm btn--dark">
                        {item.actionLabel}
                      </Link>
                    ) : (
                      <button
                        onClick={() => item.runSlug && onRunFixture(item.runSlug)}
                        disabled={!item.runSlug || isRunning}
                        className="btn btn--sm btn--dark disabled:opacity-50 disabled:cursor-wait"
                      >
                        {isRunning ? "В обработке..." : item.actionLabel}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
