"use client";

import { type ReactNode, useEffect, useMemo, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import FilterPanel from "@/components/dashboard/FilterPanel";
import RankingTable from "@/components/dashboard/RankingTable";
import StatusBadge from "@/components/dashboard/StatusBadge";
import { reviewerApi } from "@/lib/api";
import { formatPercent, formatDate } from "@/lib/utils";
import type { DashboardStats, RecommendationStatus, CandidateListItem } from "@/types";

const STATUS_LABELS: Record<RecommendationStatus, string> = {
  STRONG_RECOMMEND: "Приоритетные",
  RECOMMEND: "Рекомендованные",
  WAITLIST: "В листе ожидания",
  DECLINED: "Отклоненные",
};

const SORT_OPTIONS = [
  { value: "rpi_desc", label: "Балл: по убыванию" },
  { value: "rpi_asc", label: "Балл: по возрастанию" },
  { value: "date_desc", label: "Сначала новые" },
  { value: "confidence_desc", label: "По уверенности" },
];

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
    if (filter !== "ALL") result = result.filter((c) => c.recommendation_status === filter);
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(c => c.name.toLowerCase().includes(q) || c.selected_program.toLowerCase().includes(q));
    }
    switch (sort) {
      case "rpi_asc": result.sort((a, b) => a.review_priority_index - b.review_priority_index); break;
      case "date_desc": result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()); break;
      case "confidence_desc": result.sort((a, b) => b.confidence - a.confidence); break;
      default: result.sort((a, b) => b.review_priority_index - a.review_priority_index);
    }
    return result;
  }, [candidates, filter, sort, search]);

  const handleToggleSelect = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
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
        {/* min-w-0 предотвращает распирание флекс-контейнера таблицей */}
        <main className="flex-1 min-w-0 p-6 lg:p-10 pb-24">
          <div className="w-full"> 
            <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[800] mb-2 tracking-tighter">
              Рейтинг кандидатов
            </h1>
            <p className="text-[1rem] mb-10 text-muted">Аналитика и оценка кандидатов inVision U</p>

            {stats && (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-10">
                  {(Object.entries(stats.by_status) as [RecommendationStatus, number][]).map(([status, count]) => (
                    <div key={status} className="rounded-[1.2rem] px-6 py-6 text-center flex flex-col justify-center min-h-[120px] bg-[var(--surface-subtle)]">
                      <div className="text-[0.75rem] font-[700] uppercase tracking-[0.12em] mb-2 text-muted">{STATUS_LABELS[status]}</div>
                      <div className="text-[1.6rem] font-[800] font-numbers">{count}</div>
                    </div>
                  ))}
                  <div className="rounded-[1.2rem] px-6 py-6 text-center flex flex-col justify-center min-h-[120px] bg-[var(--surface-subtle)]">
                    <div className="text-[0.75rem] font-[700] uppercase tracking-[0.12em] mb-2 text-muted">Ср. уверенность</div>
                    <div className="text-[1.6rem] font-[800] font-numbers">{formatPercent(stats.avg_confidence)}</div>
                  </div>
                </div>

                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-6">
                  <FilterPanel activeFilter={filter} onFilterChange={setFilter} />
                  <select value={sort} onChange={(e) => setSort(e.target.value)} className="chip py-3 px-6 pr-12 font-[700] w-full lg:w-[350px]" >
                    {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 mb-8">
                  <input type="text" placeholder="Поиск кандидатов..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1 px-6 py-4 text-[1rem] font-[600] rounded-[1rem]" />
                  <div className="flex gap-1 p-1.5 rounded-[1.2rem] border border-[var(--brand-line)] w-full sm:w-[320px] shrink-0 bg-[var(--surface-subtle)]">
                    <button onClick={() => setViewMode("table")} className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${viewMode === "table" ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg" : "text-muted"}`}>Таблица</button>
                    <button onClick={() => setViewMode("grid")} className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${viewMode === "grid" ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg" : "text-muted"}`}>Карточки</button>
                  </div>
                </div>

                {/* Обертка контента с фиксированным поведением ширины */}
                <div className="w-full overflow-hidden">
                  {viewMode === "table" ? (
                    <RankingTable candidates={filtered} selected={selected} onToggleSelect={handleToggleSelect} />
                  ) : (
                    <CandidateGrid candidates={filtered} selected={selected} onToggleSelect={handleToggleSelect} />
                  )}
                </div>
              </>
            )}
          </div>
        </main>
      </div>

      {selected.size >= 2 && (
        <div className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-center gap-8 px-6 py-5 bg-[#111213] border-t border-[var(--brand-line)] backdrop-blur-xl">
          <span className="text-[1rem] font-[800] text-[var(--brand-ink)]">ВЫБРАНО {selected.size} / 3</span>
          <button onClick={() => { const ids = Array.from(selected).join(","); router.push(`/dashboard/compare?ids=${ids}`); }} className="btn py-3 px-10 text-[0.95rem] font-[800]" style={{ background: "var(--brand-blue)", color: "var(--brand-ink)" }}>Сравнить</button>
          <button onClick={() => setSelected(new Set())} className="text-[0.9rem] font-[700] text-[var(--brand-ink)] opacity-60 hover:opacity-100 transition-opacity">Сбросить</button>
        </div>
      )}
    </>
  );
}

function CandidateGrid({ candidates, selected, onToggleSelect }: { candidates: CandidateListItem[]; selected: Set<string>; onToggleSelect: (id: string) => void; }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {candidates.map((c) => (
        <div key={c.candidate_id} className="card p-6 flex flex-col transition-all duration-300 relative" style={{ outline: selected.has(c.candidate_id) ? "3px solid var(--brand-blue)" : "none", outlineOffset: "-3px" }}>
          <div className="flex justify-between items-start mb-4 gap-4">
            <div className="flex-1">
              <span className="text-[0.8rem] font-[900] text-muted font-numbers opacity-50">#{c.ranking_position}</span>
              <h3 className="text-[1.15rem] font-[900] leading-tight tracking-tight mt-1">
                <Link href={`/dashboard/${c.candidate_id}`} className="hover:underline">{c.name}</Link>
              </h3>
            </div>
            <input type="checkbox" checked={selected.has(c.candidate_id)} onChange={() => onToggleSelect(c.candidate_id)} className="accent-[var(--brand-blue)] w-5 h-5 cursor-pointer mt-1" />
          </div>
          <p className="text-[0.9rem] text-muted line-clamp-2 mb-6 h-[2.8rem] leading-relaxed">{c.selected_program}</p>
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="rounded-[1rem] p-4 bg-[var(--surface-subtle-2)]">
              <div className="text-[0.7rem] font-[800] uppercase text-muted mb-1 tracking-widest">RPI Score</div>
              <div className="text-[1.3rem] font-[800] font-numbers">{formatPercent(c.review_priority_index)}</div>
            </div>
            <div className="rounded-[1rem] p-4 bg-[var(--surface-subtle-2)]">
              <div className="text-[0.7rem] font-[800] uppercase text-muted mb-1 tracking-widest">Confidence</div>
              <div className="text-[1.3rem] font-[800] font-numbers">{formatPercent(c.confidence)}</div>
            </div>
          </div>
          <div className="mt-auto pt-5 flex items-center justify-between border-t border-[var(--brand-line)]">
            <StatusBadge status={c.recommendation_status} />
            <span className="text-[0.8rem] font-[700] text-muted font-numbers">{formatDate(c.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}