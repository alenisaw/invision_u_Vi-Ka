"use client";

import Link from "next/link";
import type { CandidateListItem } from "@/types";
import { formatPercent, formatDate } from "@/lib/utils";
import StatusBadge from "./StatusBadge";

interface RankingTableProps {
  candidates: CandidateListItem[];
}

export default function RankingTable({ candidates }: RankingTableProps) {
  if (candidates.length === 0) {
    return (
      <div className="card p-12 text-center">
        <p className="text-[1rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
          Нет кандидатов по выбранным фильтрам
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden" style={{ borderRadius: "1rem" }}>
      <table className="w-full">
        <thead>
          <tr
            className="text-left"
            style={{ borderBottom: "1px solid rgba(20, 20, 20, 0.07)" }}
          >
            <th className="eyebrow px-5 py-4">#</th>
            <th className="eyebrow px-5 py-4">Кандидат</th>
            <th className="eyebrow px-5 py-4">Программа</th>
            <th className="eyebrow px-5 py-4">Балл RPI</th>
            <th className="eyebrow px-5 py-4">Уверенность</th>
            <th className="eyebrow px-5 py-4">Статус</th>
            <th className="eyebrow px-5 py-4">Сильные стороны</th>
            <th className="eyebrow px-5 py-4">Дата</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <tr
              key={candidate.candidate_id}
              className="group transition-colors duration-[250ms]"
              style={{ borderBottom: "1px solid rgba(20, 20, 20, 0.05)" }}
            >
              <td className="px-5 py-[0.95rem]">
                <span className="text-[0.88rem] font-[800]" style={{ color: "var(--brand-muted)" }}>
                  {candidate.ranking_position}
                </span>
              </td>
              <td className="px-5 py-[0.95rem]">
                <Link
                  href={`/dashboard/${candidate.candidate_id}`}
                  className="block"
                >
                  <span className="text-[0.95rem] font-[800] hover:underline">
                    {candidate.name}
                  </span>
                  {candidate.shortlist_eligible && (
                    <span className="ml-2 text-[0.72rem] font-[700] px-2 py-0.5 rounded-full" style={{
                      background: "rgba(193, 241, 29, 0.18)",
                      color: "#415005",
                    }}>
                      Шорт-лист
                    </span>
                  )}
                </Link>
              </td>
              <td className="px-5 py-[0.95rem]">
                <span className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>
                  {candidate.selected_program.length > 30
                    ? candidate.selected_program.slice(0, 30) + "..."
                    : candidate.selected_program}
                </span>
              </td>
              <td className="px-5 py-[0.95rem]">
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(20, 20, 20, 0.06)" }}>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: formatPercent(candidate.review_priority_index),
                        background: candidate.review_priority_index >= 0.75
                          ? "var(--brand-lime)"
                          : candidate.review_priority_index >= 0.6
                            ? "var(--brand-blue)"
                            : "var(--brand-coral)",
                      }}
                    />
                  </div>
                  <span className="text-[0.88rem] font-[800]">
                    {formatPercent(candidate.review_priority_index)}
                  </span>
                </div>
              </td>
              <td className="px-5 py-[0.95rem]">
                <span className="text-[0.82rem] font-[700]" style={{ color: "var(--brand-muted-strong)" }}>
                  {formatPercent(candidate.confidence)}
                </span>
              </td>
              <td className="px-5 py-[0.95rem]">
                <StatusBadge status={candidate.recommendation_status} />
              </td>
              <td className="px-5 py-[0.95rem]">
                <div className="flex flex-wrap gap-1">
                  {candidate.top_strengths.slice(0, 2).map((s) => (
                    <span
                      key={s}
                      className="text-[0.72rem] font-[700] px-2 py-0.5 rounded-full"
                      style={{
                        background: "rgba(61, 237, 241, 0.12)",
                        color: "#0a6a6d",
                      }}
                    >
                      {s}
                    </span>
                  ))}
                  {candidate.caution_flags.length > 0 && (
                    <span
                      className="text-[0.72rem] font-[700] px-2 py-0.5 rounded-full"
                      style={{
                        background: "rgba(255, 142, 112, 0.14)",
                        color: "#ac472e",
                      }}
                    >
                      {candidate.caution_flags.length} флаг{candidate.caution_flags.length > 1 ? "а" : ""}
                    </span>
                  )}
                </div>
              </td>
              <td className="px-5 py-[0.95rem]">
                <span className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>
                  {formatDate(candidate.created_at)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
