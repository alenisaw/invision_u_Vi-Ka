"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import FilterPanel from "@/components/dashboard/FilterPanel";
import RankingTable from "@/components/dashboard/RankingTable";
import StatusBadge from "@/components/dashboard/StatusBadge";
import { reviewerApi } from "@/lib/api";
import {
  formatDate,
  formatPercent,
  localizeLabels,
  STATUS_LABELS,
} from "@/lib/utils";
import type { CandidateListItem, DashboardStats, RecommendationStatus } from "@/types";

const SORT_OPTIONS = [
  { value: "rpi_desc", label: "Бал: по убыванию" },
  { value: "rpi_asc", label: "Бал: по возрастанию" },
  { value: "date_desc", label: "Сначала новые" },
  { value: "confidence_desc", label: "По уверенности" },
] as const;

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [filter, setFilter] = useState<RecommendationStatus | "ALL">("ALL");
  const [sort, setSort] = useState("rpi_desc");
  const [search, setSearch] = useState("");
  const [viewMode, setViewMode] = useState<"table" | "grid">("table");
  const [selected, setSelected] = useState<Set<string>>(new Set());

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
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
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
      <div className="flex">
        <Sidebar />
        <main className="flex-1 min-w-0 p-6 lg:p-10 pb-24">
          <div className="w-full">
            <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[800] mb-2 tracking-tighter">
              Рейтинг кандидатов
            </h1>
            <p className="text-[1rem] mb-10 text-muted">
              Аналитика по обработанным кандидатам inVision U
            </p>

            {loading && (
              <div className="card p-12 text-center">
                <p className="text-[1rem] font-[600] text-muted">Загружаю рейтинг...</p>
              </div>
            )}

            {error && (
              <div className="card p-5 mb-8 border border-[var(--brand-coral)]/25 bg-[var(--brand-coral)]/8">
                <div className="text-[0.95rem] font-[700] text-[var(--brand-coral)]">
                  {error}
                </div>
              </div>
            )}

            {stats && !loading && (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-10">
                  {(Object.entries(stats.by_status) as [RecommendationStatus, number][]).map(
                    ([status, count]) => (
                      <div
                        key={status}
                        className="rounded-[1.2rem] px-6 py-6 text-center flex flex-col justify-center min-h-[120px] bg-[var(--surface-subtle)]"
                      >
                        <div className="text-[0.75rem] font-[700] uppercase tracking-[0.12em] mb-2 text-muted">
                          {STATUS_LABELS[status]}
                        </div>
                        <div className="text-[1.6rem] font-[800] font-numbers">{count}</div>
                      </div>
                    ),
                  )}
                  <div className="rounded-[1.2rem] px-6 py-6 text-center flex flex-col justify-center min-h-[120px] bg-[var(--surface-subtle)]">
                    <div className="text-[0.75rem] font-[700] uppercase tracking-[0.12em] mb-2 text-muted">
                      Ср. уверенность
                    </div>
                    <div className="text-[1.6rem] font-[800] font-numbers">
                      {formatPercent(stats.avg_confidence)}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-6">
                  <FilterPanel activeFilter={filter} onFilterChange={setFilter} />
                  <select
                    value={sort}
                    onChange={(event) => setSort(event.target.value)}
                    className="chip py-3 px-6 pr-12 font-[700] w-full lg:w-[350px]"
                  >
                    {SORT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 mb-8">
                  <input
                    type="text"
                    placeholder="Поиск кандидатов..."
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
                      Таблица
                    </button>
                    <button
                      onClick={() => setViewMode("grid")}
                      className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${
                        viewMode === "grid"
                          ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg"
                          : "text-muted"
                      }`}
                    >
                      Карточки
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
        </main>
      </div>

      {selected.size >= 2 && (
        <div className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-center gap-8 px-6 py-5 bg-[#111213] border-t border-[var(--brand-line)] backdrop-blur-xl">
          <span className="text-[1rem] font-[800] text-[var(--brand-ink)]">
            ВЫБРАНО {selected.size} / 3
          </span>
          <button
            onClick={() => {
              const ids = Array.from(selected).join(",");
              router.push(`/dashboard/compare?ids=${ids}`);
            }}
            className="btn py-3 px-10 text-[0.95rem] font-[800]"
            style={{ background: "var(--brand-blue)", color: "var(--brand-ink)" }}
          >
            Сравнить
          </button>
          <button
            onClick={() => setSelected(new Set())}
            className="text-[0.9rem] font-[700] text-[var(--brand-ink)] opacity-60 hover:opacity-100 transition-opacity"
          >
            Сбросить
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
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {candidates.map((candidate) => (
        <div
          key={candidate.candidate_id}
          className="card p-6 flex flex-col transition-all duration-300 relative"
          style={{
            outline: selected.has(candidate.candidate_id) ? "3px solid var(--brand-blue)" : "none",
            outlineOffset: "-3px",
          }}
        >
          <div className="flex justify-between items-start mb-4 gap-4">
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

          <p className="text-[0.9rem] text-muted line-clamp-2 mb-6 h-[2.8rem] leading-relaxed">
            {candidate.selected_program}
          </p>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <MetricCard label="Бал RPI" value={formatPercent(candidate.review_priority_index)} />
            <MetricCard label="Уверенность" value={formatPercent(candidate.confidence)} />
          </div>

          <div className="flex flex-wrap gap-2 mb-6 min-h-[2.5rem]">
            {localizeLabels(candidate.top_strengths.slice(0, 3)).map((strength) => (
              <span key={`${candidate.candidate_id}-${strength}`} className="badge badge--neutral">
                {strength}
              </span>
            ))}
          </div>

          <div className="mt-auto pt-5 flex items-center justify-between border-t border-[var(--brand-line)]">
            <StatusBadge status={candidate.recommendation_status} />
            <span className="text-[0.8rem] font-[700] text-muted font-numbers">
              {formatDate(candidate.created_at)}
            </span>
          </div>
        </div>
      ))}
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
