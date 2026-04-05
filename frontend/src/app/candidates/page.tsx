"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { LayoutGrid, List } from "lucide-react";
import Header from "@/components/layout/Header";
import CandidatePoolTable, {
  type CandidatePoolTableItem,
} from "@/components/candidate/CandidatePoolTable";
import { useLocale } from "@/components/providers/LocaleProvider";
import { reviewerApi } from "@/lib/api";
import {
  formatDate,
  localizeLabels,
  localizeProgramName,
} from "@/lib/i18n";
import type { CandidatePoolListItem } from "@/types";
import { useSearchParams } from "next/navigation";

const SORT_OPTIONS = [
  { value: "recent", key: "candidates.sort.recent" },
  { value: "rpi_desc", key: "candidates.sort.rpi_desc" },
  { value: "name_asc", key: "candidates.sort.name_asc" },
  { value: "program_asc", key: "candidates.sort.program_asc" },
] as const;

type SortValue = (typeof SORT_OPTIONS)[number]["value"];
type ViewMode = "table" | "grid";
type StageFilter = "all" | "raw" | "processed";

type CandidatePoolItem = CandidatePoolTableItem & {
  reviewPriorityIndex?: number | null;
  searchText: string;
};

function buildPoolItem(
  candidate: CandidatePoolListItem,
  viewLabel: string,
  pendingLabel: string,
  locale: "ru" | "en",
): CandidatePoolItem {
  const processed = candidate.stage === "processed";
  const qualityStatus = deriveQualityStatus(candidate);
  return {
    id: candidate.candidate_id,
    kind: processed ? "processed" : "raw",
    name: candidate.name,
    selectedProgram: candidate.selected_program,
    stageLabel: processed ? "common.processed" : "common.raw",
    qualityStatus,
    sourceQualityLabel: getSourceQualityLabel(candidate, qualityStatus, locale),
    completeness: candidate.data_completeness,
    notes: candidate.data_flags.length > 0 ? candidate.data_flags : processed ? candidate.top_strengths : [candidate.pipeline_status],
    reviewPriorityIndex: candidate.review_priority_index,
    createdAt: candidate.created_at,
    actionLabel: processed ? viewLabel : pendingLabel,
    href: processed ? `/dashboard/${candidate.candidate_id}` : undefined,
    searchText: `${candidate.name} ${candidate.selected_program} ${candidate.pipeline_status} ${candidate.data_flags.join(" ")}`.toLowerCase(),
  };
}

export default function CandidatesPage() {
  return (
    <Suspense fallback={<CandidatesPageFallback />}>
      <CandidatesPageInner />
    </Suspense>
  );
}

function CandidatesPageInner() {
  const { locale, t } = useLocale();
  const searchParams = useSearchParams();
  const highlightId = searchParams.get("highlight");

  const [pool, setPool] = useState<CandidatePoolListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortValue>("recent");
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [stageFilter, setStageFilter] = useState<StageFilter>("all");

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError("");

      try {
        const candidatePool = await reviewerApi.listCandidatePool();
        setPool(candidatePool);
      } catch (err) {
        setError(err instanceof Error ? err.message : t("candidates.loadError"));
      } finally {
        setLoading(false);
      }
    }

    void loadData();
  }, [t]);

  const items = useMemo(() => {
    const prepared = pool.map((candidate) =>
      buildPoolItem(candidate, t("candidates.action.view"), t("candidates.status.raw"), locale),
    ).map((item) => ({ ...item, stageLabel: t(item.stageLabel) }));

    const query = search.trim().toLowerCase();
    const filtered = prepared.filter((item) => {
      if (stageFilter !== "all" && item.kind !== stageFilter) {
        return false;
      }
      if (!query) {
        return true;
      }
      return item.searchText.includes(query);
    });

    return filtered.sort((left, right) => {
      if (highlightId) {
        if (left.id === highlightId && right.id !== highlightId) return -1;
        if (right.id === highlightId && left.id !== highlightId) return 1;
      }

      switch (sort) {
        case "name_asc":
          return left.name.localeCompare(right.name, locale === "ru" ? "ru" : "en");
        case "program_asc":
          return left.selectedProgram.localeCompare(right.selectedProgram, locale === "ru" ? "ru" : "en");
        case "rpi_desc":
          return (right.reviewPriorityIndex ?? -1) - (left.reviewPriorityIndex ?? -1);
        case "recent":
        default:
          return new Date(right.createdAt ?? 0).getTime() - new Date(left.createdAt ?? 0).getTime();
      }
    });
  }, [highlightId, locale, pool, search, sort, stageFilter, t]);

  const stats = useMemo(
    () => ({
      total: pool.length,
      processed: pool.filter((item) => item.stage === "processed").length,
      raw: pool.filter((item) => item.stage === "raw").length,
    }),
    [pool],
  );

  return (
    <>
      <Header />
      <main className="min-w-0 px-5 py-6 lg:px-8 lg:py-8 pb-24 relative">
        <div className="container-app page-shell">
            <div className="page-stack">
            <div>
              <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[900] tracking-[-0.05em]">
                {t("candidates.title")}
              </h1>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <StatCard label={t("candidates.total")} value={String(stats.total)} tone="lime" />
              <StatCard label={t("candidates.processed")} value={String(stats.processed)} tone="blue" />
              <StatCard label={t("candidates.raw")} value={String(stats.raw)} tone="neutral" />
            </div>

            <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
              <div className="flex flex-wrap gap-2">
                <FilterChip active={stageFilter === "all"} onClick={() => setStageFilter("all")} label={t("common.all")} />
                <FilterChip active={stageFilter === "raw"} onClick={() => setStageFilter("raw")} label={t("common.raw")} />
                <FilterChip active={stageFilter === "processed"} onClick={() => setStageFilter("processed")} label={t("common.processed")} />
              </div>

              <select
                value={sort}
                onChange={(event) => setSort(event.target.value as SortValue)}
                className="chip py-3 px-6 pr-16 font-[700] w-full xl:w-[320px] appearance-none outline-none cursor-pointer transition-all"
                style={{
                  backgroundImage:
                    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E\")",
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 1.5rem center",
                  backgroundSize: "1rem",
                }}
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {t(option.key)}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={t("candidates.searchPlaceholder")}
                className="flex-1 px-6 py-4 text-[1rem] font-[600] rounded-[1rem] bg-[var(--surface-subtle)] border border-[var(--brand-line)] outline-none focus:ring-2 focus:ring-[var(--brand-blue)]"
              />
              <div className="flex gap-1 p-1.5 rounded-[1.2rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] shrink-0 w-full sm:w-[320px]">
                <button
                  onClick={() => setViewMode("table")}
                  className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${
                    viewMode === "table"
                      ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg"
                      : "text-muted hover:bg-[var(--surface-hover)]"
                  }`}
                >
                  <span className="inline-flex items-center justify-center gap-2">
                    <List className="h-4 w-4" />
                    {t("common.list")}
                  </span>
                </button>
                <button
                  onClick={() => setViewMode("grid")}
                  className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${
                    viewMode === "grid"
                      ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg"
                      : "text-muted hover:bg-[var(--surface-hover)]"
                  }`}
                >
                  <span className="inline-flex items-center justify-center gap-2">
                    <LayoutGrid className="h-4 w-4" />
                    {t("common.grid")}
                  </span>
                </button>
              </div>
            </div>

            {error && (
              <div className="card p-5 border border-[var(--brand-coral)]/25 bg-[var(--brand-coral)]/8">
                <div className="text-[0.95rem] font-[700] text-[var(--brand-coral)]">
                  {error}
                </div>
              </div>
            )}

            {loading ? (
              <div className="card p-12 text-center text-muted font-[700]">
                {t("candidates.loading")}
              </div>
            ) : viewMode === "table" ? (
              <CandidatePoolTable items={items} highlightedId={highlightId} />
            ) : items.length === 0 ? (
              <div className="card p-12 text-center">
                <p className="text-[1rem] font-[600] text-muted">{t("candidates.noResults")}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {items.map((item) => {
                  const isHighlighted = highlightId === item.id;
                  const localizedNotes = localizeLabels(item.notes.slice(0, 3), locale);

                  return (
                    <div
                      key={item.id}
                      className="card p-7 flex flex-col h-full transition-all duration-300 hover:-translate-y-1 min-h-[22rem]"
                      style={{
                        outline: isHighlighted ? "3px solid var(--brand-blue)" : "none",
                        outlineOffset: "-3px",
                      }}
                    >
                      <div className="mb-5 min-h-[5.75rem]">
                        <h3 className="text-[1.15rem] font-[900] leading-tight tracking-tight mb-3 min-h-[2.75rem]">
                          {item.name}
                        </h3>
                        <span className={`badge ${item.kind === "processed" ? "badge--blue" : "badge--neutral"}`}>
                          {item.stageLabel}
                        </span>
                      </div>

                      <p className="text-[0.95rem] text-muted line-clamp-2 mb-6 min-h-[3rem] leading-relaxed">
                        {localizeProgramName(item.selectedProgram, locale)}
                      </p>

                      <div className="mb-4">
                        <span className={`badge ${getQualityBadge(item.qualityStatus)}`}>
                          {item.sourceQualityLabel}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 gap-3 mb-6">
                        <MetricCard
                          label={t("candidates.table.completeness")}
                          value={item.completeness != null ? `${Math.round(item.completeness * 100)}%` : t("candidates.completeness.pending")}
                        />
                      </div>

                      <div className="flex flex-wrap content-start gap-2 mb-7 min-h-[4rem]">
                        {localizedNotes.length > 0 ? (
                          localizedNotes.map((note) => (
                            <span key={`${item.id}-${note}`} className="badge badge--neutral">
                              {note}
                            </span>
                          ))
                        ) : (
                          <span className="text-[0.82rem] text-muted">{t("candidates.notes.empty")}</span>
                        )}
                      </div>

                      <div className="mt-auto pt-5 flex items-center justify-between border-t border-[var(--brand-line)] gap-3">
                        <span className="text-[0.8rem] font-[700] text-muted font-numbers">
                          {item.createdAt ? formatDate(item.createdAt, locale) : t("common.unknownDate")}
                        </span>
                        {item.href ? (
                          <a href={item.href} className="btn btn--sm btn--dark">
                            {item.actionLabel}
                          </a>
                        ) : (
                          <div className="btn btn--ghost btn--sm cursor-default opacity-70">
                            {item.actionLabel}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            </div>
        </div>
      </main>
    </>
  );
}

function CandidatesPageFallback() {
  const content = (
    <>
      <Header />
      <main className="min-w-0 p-6 lg:p-10 pb-24 relative">
        <div className="container-app">
          <div className="card p-12 text-center text-muted font-[700]">
            Loading...
          </div>
        </div>
      </main>
    </>
  );

  return content;
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "lime" | "blue" | "neutral";
}) {
  const background =
    tone === "lime"
      ? "rgba(193, 241, 29, 0.16)"
      : tone === "blue"
        ? "rgba(61, 237, 241, 0.14)"
        : "var(--surface-subtle)";

  return (
    <div className="rounded-[1.2rem] px-6 py-6 bg-[var(--surface-subtle)]" style={{ background }}>
      <div className="text-[0.75rem] font-[700] uppercase tracking-[0.12em] mb-2 text-muted">
        {label}
      </div>
      <div className="text-[1.7rem] font-[800] font-numbers">{value}</div>
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button onClick={onClick} className={`chip ${active ? "is-active" : ""}`}>
      {label}
    </button>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1rem] p-4 bg-[var(--surface-subtle-2)]">
      <div className="text-[0.7rem] font-[800] uppercase text-muted mb-1 tracking-widest">
        {label}
      </div>
      <div className="text-[1.2rem] font-[800] font-numbers">{value}</div>
    </div>
  );
}

function deriveQualityStatus(candidate: CandidatePoolListItem) {
  const flags = new Set([...(candidate.data_flags ?? []), ...(candidate.caution_flags ?? [])]);
  if (candidate.stage === "raw") return "pending" as const;
  if (
    flags.has("asr_processing_failed") ||
    flags.has("empty_signal_envelope") ||
    flags.has("no_structured_signals")
  ) {
    return "degraded" as const;
  }
  if (
    flags.has("low_asr_confidence") ||
    flags.has("speech_authenticity_risk") ||
    flags.has("possible_ai_use") ||
    flags.has("authenticity_or_ai_risk") ||
    flags.has("low_cross_source_consistency")
  ) {
    return "partial" as const;
  }
  return "healthy" as const;
}

function getSourceQualityLabel(
  candidate: CandidatePoolListItem,
  status: ReturnType<typeof deriveQualityStatus>,
  locale: "ru" | "en",
) {
  if (candidate.stage === "raw") {
    return locale === "ru" ? "Ожидает обработки" : "Pending processing";
  }
  if (status === "healthy") {
    return locale === "ru" ? "Источник подтвержден" : "Source healthy";
  }
  if (status === "degraded") {
    return locale === "ru" ? "Сниженное качество" : "Degraded source";
  }
  return locale === "ru" ? "Нужна проверка" : "Needs review";
}

function getQualityBadge(status?: CandidatePoolItem["qualityStatus"]) {
  if (status === "healthy") return "badge--lime";
  if (status === "degraded") return "badge--coral";
  if (status === "partial") return "badge--blue";
  return "badge--neutral";
}
