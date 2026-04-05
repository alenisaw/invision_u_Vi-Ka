"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LayoutGrid, List } from "lucide-react";
import Header from "@/components/layout/Header";
import { useLocale } from "@/components/providers/LocaleProvider";
import FilterPanel from "@/components/dashboard/FilterPanel";
import RankingTable from "@/components/dashboard/RankingTable";
import StatusBadge from "@/components/dashboard/StatusBadge";
import { reviewerApi } from "@/lib/api";
import {
  formatDate,
  formatPercent,
  getAiRiskLevel,
  localizeLabels,
  getStatusLabel,
} from "@/lib/i18n";
import type { CandidateListItem, DashboardStats, RecommendationStatus } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const { locale, t } = useLocale();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [filter, setFilter] = useState<RecommendationStatus | "ALL">("ALL");
  const [sort, setSort] = useState("rpi_desc");
  const [search, setSearch] = useState("");
  const [viewMode, setViewMode] = useState<"table" | "grid">("table");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const sortOptions = [
    { value: "rpi_desc", label: t("dashboard.sort.rpi_desc") },
    { value: "rpi_asc", label: t("dashboard.sort.rpi_asc") },
    { value: "date_desc", label: t("dashboard.sort.date_desc") },
    { value: "confidence_desc", label: t("dashboard.sort.confidence_desc") },
  ] as const;

  useEffect(() => {
    void loadDashboard();
  }, []);

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [nextStats, nextCandidates] = await Promise.all([
        reviewerApi.getDashboardStats(),
        reviewerApi.listDashboardCandidates(),
      ]);
      setStats(nextStats);
      setCandidates(nextCandidates);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("dashboard.loadError"));
    } finally {
      setLoading(false);
    }
  }

  const filtered = useMemo(() => {
    let result = [...candidates];

    if (filter !== "ALL") {
      result = result.filter((candidate) => candidate.recommendation_status === filter);
    }

    if (search.trim()) {
      const query = search.toLowerCase();
      result = result.filter(
        (candidate) =>
          candidate.name.toLowerCase().includes(query) ||
          candidate.selected_program.toLowerCase().includes(query),
      );
    }

    switch (sort) {
      case "rpi_asc":
        result.sort((left, right) => left.review_priority_index - right.review_priority_index);
        break;
      case "date_desc":
        result.sort(
          (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
        );
        break;
      case "confidence_desc":
        result.sort((left, right) => right.confidence - left.confidence);
        break;
      default:
        result.sort((left, right) => right.review_priority_index - left.review_priority_index);
        break;
    }

    return result;
  }, [candidates, filter, search, sort]);

  const handleToggleSelect = useCallback((id: string) => {
    setSelected((previous) => {
      const next = new Set(previous);
      if (next.has(id)) next.delete(id);
      else if (next.size < 3) next.add(id);
      return next;
    });
  }, []);

  return (
    <>
      <Header />
      <main className="min-w-0 px-5 py-6 lg:px-8 lg:py-8 pb-24">
        <div className="container-app page-shell">
          <div className="page-stack">
            <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[800] tracking-tighter">
              {t("dashboard.title")}
            </h1>

            {loading && (
              <div className="card p-12 text-center">
                <p className="text-[1rem] font-[600] text-muted">{t("dashboard.loading")}</p>
              </div>
            )}

            {error && (
              <div className="card p-5 border border-[var(--brand-coral)]/25 bg-[var(--brand-coral)]/8">
                <div className="text-[0.95rem] font-[700] text-[var(--brand-coral)]">
                  {error}
                </div>
              </div>
            )}

            {stats && !loading && (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                  {(Object.entries(stats.by_status) as [RecommendationStatus, number][]).map(
                    ([status, count], index) => (
                      <div
                        key={status}
                        className="rounded-[1.2rem] px-6 py-6 text-center flex flex-col justify-center min-h-[120px] bg-[var(--surface-subtle)]"
                        style={{
                          background:
                            index === 0
                              ? "linear-gradient(180deg, rgba(193, 241, 29, 0.22), var(--surface-subtle))"
                              : index === 1
                                ? "linear-gradient(180deg, rgba(61, 237, 241, 0.2), var(--surface-subtle))"
                                : index === 2
                                  ? "linear-gradient(180deg, rgba(255, 154, 121, 0.16), var(--surface-subtle))"
                                  : "linear-gradient(180deg, rgba(255,255,255,0.02), var(--surface-subtle))",
                        }}
                      >
                        <div className="text-[0.75rem] font-[700] uppercase tracking-[0.12em] mb-2 text-muted">
                          {getStatusLabel(status, locale)}
                        </div>
                        <div className="text-[1.6rem] font-[800] font-numbers">{count}</div>
                      </div>
                    ),
                  )}
                  <div className="rounded-[1.2rem] px-6 py-6 text-center flex flex-col justify-center min-h-[120px] bg-[var(--surface-subtle)]">
                    <div className="text-[0.75rem] font-[700] uppercase tracking-[0.12em] mb-2 text-muted">
                      {t("dashboard.avgConfidence")}
                    </div>
                    <div className="text-[1.6rem] font-[800] font-numbers">
                      {formatPercent(stats.avg_confidence)}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                  <FilterPanel activeFilter={filter} onFilterChange={setFilter} />
                  <select
                    value={sort}
                    onChange={(event) => setSort(event.target.value)}
                    className="chip py-3 px-6 pr-12 font-[700] w-full lg:w-[320px]"
                  >
                    {sortOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col sm:flex-row gap-4">
                  <input
                    type="text"
                    placeholder={t("dashboard.searchPlaceholder")}
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    className="flex-1 px-6 py-4 text-[1rem] font-[600] rounded-[1rem]"
                  />
                  <div className="flex gap-1 p-1.5 rounded-[1.2rem] border border-[var(--brand-line)] w-full sm:w-[320px] shrink-0 bg-[var(--surface-subtle)]">
                    <button
                      onClick={() => setViewMode("table")}
                      className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${
                        viewMode === "table"
                          ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg"
                          : "text-muted"
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
                          : "text-muted"
                      }`}
                    >
                      <span className="inline-flex items-center justify-center gap-2">
                        <LayoutGrid className="h-4 w-4" />
                        {t("common.grid")}
                      </span>
                    </button>
                  </div>
                </div>

                <div className="w-full overflow-hidden">
                  {viewMode === "table" ? (
                    <RankingTable
                      candidates={filtered}
                      selected={selected}
                      onToggleSelect={handleToggleSelect}
                    />
                  ) : filtered.length === 0 ? (
                    <div className="card p-12 text-center">
                      <p className="text-[1rem] font-[600] text-muted">
                        {t("dashboard.emptyFiltered")}
                      </p>
                    </div>
                  ) : (
                    <CandidateGrid
                      candidates={filtered}
                      selected={selected}
                      onToggleSelect={handleToggleSelect}
                    />
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      {selected.size >= 2 && (
        <div className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-center gap-8 px-6 py-5 bg-[#111213] border-t border-[var(--brand-line)] backdrop-blur-xl">
          <span className="text-[1rem] font-[800] text-[var(--brand-ink)]">
            {t("dashboard.selectedCount", { count: selected.size })}
          </span>
          <button
            onClick={() => {
              const ids = Array.from(selected).join(",");
              router.push(`/dashboard/compare?ids=${ids}`);
            }}
            className="btn py-3 px-10 text-[0.95rem] font-[800]"
            style={{ background: "var(--brand-blue)", color: "var(--brand-ink)" }}
          >
            {t("dashboard.compare")}
          </button>
          <button
            onClick={() => setSelected(new Set())}
            className="text-[0.9rem] font-[700] text-[var(--brand-ink)] opacity-60 hover:opacity-100 transition-opacity"
          >
            {t("dashboard.reset")}
          </button>
        </div>
      )}
    </>
  );
}

function CandidateGrid({
  candidates,
  selected,
  onToggleSelect,
}: {
  candidates: CandidateListItem[];
  selected: Set<string>;
  onToggleSelect: (id: string) => void;
}) {
  const { locale, t } = useLocale();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {candidates.map((candidate) => (
        <div
          key={candidate.candidate_id}
          className="card p-7 flex flex-col transition-all duration-300 relative min-h-[27rem]"
          style={{
            outline: selected.has(candidate.candidate_id) ? "3px solid var(--brand-blue)" : "none",
            outlineOffset: "-3px",
          }}
        >
          <div className="flex justify-between items-start mb-5 gap-4">
            <div className="flex-1">
              <span className="text-[0.8rem] font-[900] text-muted font-numbers opacity-50">
                #{candidate.ranking_position}
              </span>
              <h3 className="text-[1.15rem] font-[900] leading-tight tracking-tight mt-1">
                <Link href={`/dashboard/${candidate.candidate_id}`} className="hover:underline">
                  {candidate.name}
                </Link>
              </h3>
            </div>
            <input
              type="checkbox"
              checked={selected.has(candidate.candidate_id)}
              onChange={() => onToggleSelect(candidate.candidate_id)}
              className="accent-[var(--brand-blue)] w-5 h-5 cursor-pointer mt-1"
            />
          </div>

          <p className="text-[0.95rem] text-muted line-clamp-2 mb-7 min-h-[3rem] leading-relaxed">
            {candidate.selected_program}
          </p>

          <div className="grid grid-cols-2 gap-3 mb-5">
            <MetricCard label={t("dashboard.rpiScore")} value={formatPercent(candidate.review_priority_index)} />
            <MetricCard label={t("common.confidence")} value={formatPercent(candidate.confidence)} />
          </div>

          <AiRiskCard flags={candidate.caution_flags} />

          <div className="flex flex-wrap content-start gap-2 mb-7 min-h-[4.25rem]">
            {localizeLabels(candidate.top_strengths.slice(0, 3), locale).map((strength) => (
              <span key={`${candidate.candidate_id}-${strength}`} className="badge badge--neutral">
                {strength}
              </span>
            ))}
          </div>

          <div className="mt-auto pt-5 flex items-center justify-between border-t border-[var(--brand-line)] gap-4">
            <StatusBadge status={candidate.recommendation_status} />
            <span className="text-[0.8rem] font-[700] text-muted font-numbers">
              {formatDate(candidate.created_at, locale)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function AiRiskCard({ flags }: { flags: string[] }) {
  const { t } = useLocale();
  const risk = getAiRiskLevel(flags);
  const toneClass =
    risk === "high"
      ? "badge badge--coral"
      : risk === "review"
        ? "badge badge--neutral"
        : "badge badge--blue";

  return (
    <div className="mb-5 rounded-[1rem] border border-[var(--brand-line)] bg-[linear-gradient(180deg,var(--surface-soft),var(--surface-subtle))] px-4 py-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
          {t("dashboard.aiRisk")}
        </div>
        <span className={toneClass}>{t(`dashboard.aiRisk.${risk}`)}</span>
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1rem] p-4 bg-[var(--surface-subtle-2)]">
      <div className="text-[0.7rem] font-[800] uppercase text-muted mb-1 tracking-widest">
        {label}
      </div>
      <div className="text-[1.3rem] font-[800] font-numbers">{value}</div>
    </div>
  );
}
