"use client";

import Link from "next/link";
import { useLocale } from "@/components/providers/LocaleProvider";
import { formatDate, formatPercent, localizeLabels, localizeProgramName } from "@/lib/i18n";

export interface CandidatePoolTableItem {
  id: string;
  kind: "processed" | "raw";
  name: string;
  selectedProgram: string;
  stageLabel: string;
  qualityStatus?: "healthy" | "degraded" | "partial" | "pending";
  sourceQualityLabel?: string;
  completeness?: number | null;
  notes: string[];
  createdAt?: string | null;
  actionLabel: string;
  href?: string;
}

interface CandidatePoolTableProps {
  items: CandidatePoolTableItem[];
  highlightedId?: string | null;
}

export default function CandidatePoolTable({
  items,
  highlightedId,
}: CandidatePoolTableProps) {
  const { locale, t } = useLocale();

  if (items.length === 0) {
    return (
      <div className="card p-12 text-center">
        <p className="text-[1rem] font-[600] text-muted">{t("candidates.noResults")}</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden rounded-[1.2rem]">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px]">
          <thead>
            <tr className="text-left" style={{ borderBottom: "1px solid var(--brand-line)" }}>
              <th className="eyebrow px-6 py-5">{t("candidates.table.candidate")}</th>
              <th className="eyebrow px-6 py-5">{t("candidates.table.program")}</th>
              <th className="eyebrow px-6 py-5">
                {locale === "ru" ? "Качество источника" : "Source quality"}
              </th>
              <th className="eyebrow px-6 py-5">{t("candidates.table.completeness")}</th>
              <th className="eyebrow px-6 py-5">{t("candidates.table.notes")}</th>
              <th className="eyebrow px-6 py-5 w-[148px]">{t("candidates.table.date")}</th>
              <th className="eyebrow px-6 py-5">{t("candidates.table.action")}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const isHighlighted = highlightedId === item.id;
              const localizedNotes = localizeLabels(item.notes.slice(0, 3), locale);

              return (
                <tr
                  key={item.id}
                  className={`transition-colors duration-[250ms] ${isHighlighted ? "bg-[var(--surface-subtle-2)]" : ""}`}
                  style={{ borderBottom: "1px solid var(--brand-line)" }}
                >
                  <td className="px-6 py-[1.15rem] align-top">
                    <div className="flex flex-col gap-1.5">
                      <span className="text-[0.98rem] font-[800] leading-tight">{item.name}</span>
                      <span className={`badge ${item.kind === "processed" ? "badge--blue" : "badge--neutral"}`}>
                        {item.stageLabel}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-[1.15rem] align-top">
                    <span className="text-[0.84rem] text-muted-strong">
                      {localizeProgramName(item.selectedProgram, locale)}
                    </span>
                  </td>
                  <td className="px-6 py-[1.15rem] align-top">
                    <div className="flex flex-col gap-2">
                      <span className={`badge ${getQualityBadge(item.qualityStatus)}`}>
                        {item.sourceQualityLabel ?? (locale === "ru" ? "В обработке" : "Pending")}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-[1.15rem] align-top">
                    <div className="flex flex-col gap-1">
                      <span className="text-[0.96rem] font-[800] font-numbers">
                        {item.completeness != null ? formatPercent(item.completeness) : t("candidates.completeness.pending")}
                      </span>
                      <span className="text-[0.76rem] text-muted">{t("candidates.completeness.helper")}</span>
                    </div>
                  </td>
                  <td className="px-6 py-[1.15rem] align-top">
                    <div className="flex flex-wrap gap-1.5">
                      {localizedNotes.length > 0 ? (
                        localizedNotes.map((note) => (
                          <span
                            key={`${item.id}-${note}`}
                            className="text-[0.72rem] font-[700] px-2 py-0.5 rounded-full bg-[var(--surface-subtle-2)] text-[var(--brand-muted-strong)]"
                          >
                            {note}
                          </span>
                        ))
                      ) : (
                        <span className="text-[0.8rem] text-muted">{t("candidates.notes.empty")}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-[1.15rem] whitespace-nowrap align-top">
                    <span className="text-[0.82rem] text-muted font-numbers">
                      {item.createdAt ? formatDate(item.createdAt, locale) : t("common.unknownDate")}
                    </span>
                  </td>
                  <td className="px-6 py-[1.15rem] align-top">
                    {item.href ? (
                      <Link href={item.href} className="btn btn--sm btn--dark w-full justify-center text-center">
                        {item.actionLabel}
                      </Link>
                    ) : (
                      <div className="btn btn--ghost btn--sm w-full justify-center text-center cursor-default opacity-70">
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

function getQualityBadge(status?: CandidatePoolTableItem["qualityStatus"]) {
  if (status === "healthy") return "badge--lime";
  if (status === "degraded") return "badge--coral";
  if (status === "partial") return "badge--blue";
  return "badge--neutral";
}
