"use client";

import Link from "next/link";
import { useLocale } from "@/components/providers/LocaleProvider";
import {
  formatDate,
  formatPercent,
  localizeLabels,
  localizeProgramName,
} from "@/lib/i18n";
import type { RecommendationStatus } from "@/types";
import StatusBadge from "@/components/dashboard/StatusBadge";

export interface CandidatePoolTableItem {
  id: string;
  kind: "processed" | "raw";
  name: string;
  selectedProgram: string;
  sourceLabel: string;
  sourceTone: "lime" | "blue" | "neutral";
  statusLabel: string;
  recommendationStatus?: RecommendationStatus | null;
  reviewPriorityIndex?: number | null;
  confidence?: number | null;
  tags: string[];
  createdAt?: string | null;
  actionLabel: string;
  href?: string;
}

interface CandidatePoolTableProps {
  items: CandidatePoolTableItem[];
  highlightedId?: string | null;
}

const SOURCE_TONE_CLASS: Record<CandidatePoolTableItem["sourceTone"], string> = {
  lime: "badge--lime",
  blue: "badge--blue",
  neutral: "badge--neutral",
};

export default function CandidatePoolTable({
  items,
  highlightedId,
}: CandidatePoolTableProps) {
  const { locale, t } = useLocale();

  if (items.length === 0) {
    return (
      <div className="card p-12 text-center">
        <p className="text-[1rem] font-[600] text-muted">
          {t("candidates.noResults")}
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
              <th className="eyebrow px-5 py-4">{t("candidates.table.candidate")}</th>
              <th className="eyebrow px-5 py-4">{t("candidates.table.program")}</th>
              <th className="eyebrow px-5 py-4">{t("candidates.table.source")}</th>
              <th className="eyebrow px-5 py-4">{t("candidates.table.status")}</th>
              <th className="eyebrow px-5 py-4">{t("candidates.table.metrics")}</th>
              <th className="eyebrow px-5 py-4">{t("candidates.table.tags")}</th>
              <th className="eyebrow px-5 py-4 w-[140px]">{t("candidates.table.date")}</th>
              <th className="eyebrow px-5 py-4">{t("candidates.table.action")}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const isHighlighted = highlightedId === item.id;
              const localizedTags = localizeLabels(item.tags.slice(0, 3), locale);

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
                        {item.kind === "processed" ? t("candidates.status.processed") : t("candidates.status.raw")}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-[1rem]">
                    <span className="text-[0.84rem] text-muted-strong">
                      {localizeProgramName(item.selectedProgram, locale)}
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
                          : t("candidates.metrics.pending")}
                      </span>
                      <span className="text-[0.82rem] font-[700] text-muted">
                        {item.confidence != null
                          ? `${t("common.confidence")} ${formatPercent(item.confidence)}`
                          : t("candidates.metrics.noConfidence")}
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
                        <span className="text-[0.8rem] text-muted">{t("common.none")}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-[1rem] whitespace-nowrap">
                    <span className="text-[0.82rem] text-muted font-numbers">
                      {item.createdAt ? formatDate(item.createdAt, locale) : t("common.unknownDate")}
                    </span>
                  </td>
                  <td className="px-5 py-[1rem]">
                    {item.href ? (
                      <Link href={item.href} className="btn btn--sm btn--dark w-full justify-start text-left">
                        {item.actionLabel}
                      </Link>
                    ) : (
                      <div className="btn btn--ghost btn--sm w-full justify-start text-left cursor-default opacity-70">
                        {item.actionLabel}
                      </div>
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
