"use client";

import Link from "next/link";
import { useLocale } from "@/components/providers/LocaleProvider";
import type { CandidateListItem } from "@/types";
import { formatDate, formatPercent, localizeLabels, translate } from "@/lib/i18n";
import {
  derivePipelineDisplayStatus,
  getAuthenticityAdvisoryBadge,
  getAuthenticityAdvisoryLabel,
  getPipelineStatusBadge,
  getPipelineStatusLabel,
  hasAuthenticityAdvisory,
} from "@/lib/pipeline-ui";
import StatusBadge from "./StatusBadge";

interface RankingTableProps {
  candidates: CandidateListItem[];
  selected: Set<string>;
  onToggleSelect: (id: string) => void;
}

export default function RankingTable({ candidates, selected, onToggleSelect }: RankingTableProps) {
  const { locale, t } = useLocale();

  if (candidates.length === 0) {
    return (
      <div className="card p-12 text-center">
        <p className="text-[1rem] font-[600] text-muted">{t("dashboard.emptyFiltered")}</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden rounded-[1rem]" data-testid="ranking-table">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px]">
          <thead>
            <tr className="text-left" style={{ borderBottom: "1px solid var(--brand-line)" }}>
              <th className="px-5 py-4 w-12"></th>
              <th className="eyebrow px-5 py-4">{t("dashboard.table.number")}</th>
              <th className="eyebrow px-5 py-4">{t("dashboard.table.candidate")}</th>
              <th className="eyebrow px-5 py-4">{t("dashboard.table.program")}</th>
              <th className="eyebrow px-5 py-4">
                {locale === "ru" ? "Оценка кандидата" : "Candidate score"}
              </th>
              <th className="eyebrow px-5 py-4 text-center">{t("common.confidence")}</th>
              <th className="eyebrow px-5 py-4">{t("dashboard.table.status")}</th>
              <th className="eyebrow px-5 py-4">{t("dashboard.table.strengths")}</th>
              <th className="eyebrow px-5 py-4 w-[140px]">{t("dashboard.table.date")}</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((candidate) => {
              const strengths = localizeLabels(candidate.top_strengths.slice(0, 2), locale);
              const qualityStatus = derivePipelineDisplayStatus(candidate.caution_flags);
              const showAuthenticity = hasAuthenticityAdvisory(candidate.caution_flags);

              return (
                <tr
                  key={candidate.candidate_id}
                  data-testid={`candidate-row-${candidate.candidate_id}`}
                  className={`group transition-colors duration-[250ms] ${
                    selected.has(candidate.candidate_id) ? "bg-[var(--surface-subtle-2)]" : ""
                  }`}
                  style={{ borderBottom: "1px solid var(--brand-line)" }}
                >
                  <td className="px-5 py-[0.95rem]">
                    <input
                      type="checkbox"
                      checked={selected.has(candidate.candidate_id)}
                      onChange={() => onToggleSelect(candidate.candidate_id)}
                      className="accent-[var(--brand-blue)] w-4 h-4 cursor-pointer"
                    />
                  </td>
                  <td className="px-5 py-[0.95rem]">
                    <span className="text-[0.88rem] font-[700] text-muted font-numbers">
                      {candidate.ranking_position}
                    </span>
                  </td>
                  <td className="px-5 py-[0.95rem]">
                    <Link href={`/dashboard/${candidate.candidate_id}`} className="block">
                      <span className="text-[0.95rem] font-[700] hover:underline">{candidate.name}</span>
                    </Link>
                  </td>
                  <td className="px-5 py-[0.95rem]">
                    <span className="text-[0.82rem] text-muted">
                      {candidate.selected_program.length > 30
                        ? `${candidate.selected_program.slice(0, 30)}...`
                        : candidate.selected_program}
                    </span>
                  </td>
                  <td className="px-5 py-[0.95rem]">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-16 h-1.5 rounded-full overflow-hidden"
                        style={{ background: "var(--surface-subtle-2)" }}
                      >
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: formatPercent(candidate.review_priority_index),
                            background:
                              candidate.review_priority_index >= 0.75
                                ? "var(--brand-lime)"
                                : candidate.review_priority_index >= 0.6
                                  ? "var(--brand-blue)"
                                  : "var(--brand-coral)",
                          }}
                        />
                      </div>
                      <span className="text-[0.88rem] font-[700] font-numbers">
                        {formatPercent(candidate.review_priority_index)}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-[0.95rem] text-center">
                    <span className="text-[0.82rem] font-[700] text-muted-strong font-numbers">
                      {formatPercent(candidate.confidence)}
                    </span>
                  </td>
                  <td className="px-5 py-[0.95rem]">
                    <div className="flex flex-wrap gap-2">
                      <StatusBadge status={candidate.recommendation_status} />
                      <span className={`badge ${getPipelineStatusBadge(qualityStatus)}`}>
                        {getPipelineStatusLabel(qualityStatus, locale)}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-[0.95rem]">
                    <div className="flex flex-wrap gap-1">
                      {strengths.map((strength) => (
                        <span
                          key={strength}
                          className="text-[0.72rem] font-[700] px-2 py-0.5 rounded-full bg-[var(--badge-blue-bg)] text-[var(--badge-blue-text)]"
                        >
                          {strength}
                        </span>
                      ))}
                      {candidate.caution_flags.length > 0 && (
                        <span className="text-[0.72rem] font-[700] px-2 py-0.5 rounded-full bg-[var(--badge-coral-bg)] text-[var(--badge-coral-text)] font-numbers">
                          {translate(locale, "dashboard.flagsCount", {
                            count: candidate.caution_flags.length,
                          })}
                        </span>
                      )}
                      {showAuthenticity ? (
                        <span className={`text-[0.72rem] font-[700] px-2 py-0.5 rounded-full ${getAuthenticityAdvisoryBadge(candidate.caution_flags)}`}>
                          {getAuthenticityAdvisoryLabel(candidate.caution_flags, locale)}
                        </span>
                      ) : null}
                    </div>
                  </td>
                  <td className="px-5 py-[0.95rem] whitespace-nowrap">
                    <span className="text-[0.82rem] text-muted font-numbers">
                      {formatDate(candidate.created_at, locale)}
                    </span>
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
