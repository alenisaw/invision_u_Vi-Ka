"use client";

import { type ReactNode, useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import FilterPanel from "@/components/dashboard/FilterPanel";
import RankingTable from "@/components/dashboard/RankingTable";
import { reviewerApi } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import type { DashboardStats, RecommendationStatus, CandidateListItem } from "@/types";

const STATUS_LABELS: Record<RecommendationStatus, string> = {
  STRONG_RECOMMEND: "Сильная рекомендация",
  RECOMMEND: "Рекомендованы",
  WAITLIST: "Лист ожидания",
  DECLINED: "Отклонены",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<RecommendationStatus | "ALL">("ALL");
  const [sort, setSort] = useState("rpi_desc");
  const [search, setSearch] = useState("");

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
      setError(
        err instanceof Error ? err.message : "Не удалось загрузить данные дашборда.",
      );
    } finally {
      setLoading(false);
    }
  }

  const filtered = useMemo(() => {
    let result = [...candidates];

    if (filter !== "ALL") {
      result = result.filter((c) => c.recommendation_status === filter);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.selected_program.toLowerCase().includes(q)
      );
    }

    switch (sort) {
      case "rpi_asc":
        result.sort((a, b) => a.review_priority_index - b.review_priority_index);
        break;
      case "date_desc":
        result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
      case "confidence_desc":
        result.sort((a, b) => b.confidence - a.confidence);
        break;
      default:
        result.sort((a, b) => b.review_priority_index - a.review_priority_index);
    }

    return result;
  }, [candidates, filter, sort, search]);

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8">
          <div className="container-app">
            <h1
              className="text-[clamp(2rem,1.65rem+1.8vw,3.2rem)] font-[800] mb-2"
              style={{ letterSpacing: "-0.04em" }}
            >
              Рейтинг кандидатов
            </h1>
            <p className="text-[0.95rem] mb-8" style={{ color: "var(--brand-muted)" }}>
              Панель оценки кандидатов с помощью ИИ для приёмной комиссии inVision U
            </p>

            {loading && !stats ? (
              <DashboardStateCard
                title="Загружаем данные кандидатов"
                description="Подтягиваем статистику, рейтинг и reviewer-данные из backend."
              />
            ) : error && !stats ? (
              <DashboardStateCard
                title="Не удалось загрузить дашборд"
                description={error}
                action={
                  <button onClick={() => void loadDashboard()} className="btn btn--dark btn--sm">
                    Повторить
                  </button>
                }
              />
            ) : stats ? (
              <>
            {/* Summary strip */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
              <SummaryCard label="Всего" value={stats.total_candidates} />
              <SummaryCard label="Обработано" value={stats.processed} />
              <SummaryCard label="Шорт-лист" value={stats.shortlisted} accent />
              <SummaryCard label="Ожидают проверки" value={stats.pending_review} />
              <SummaryCard label="Ср. уверенность" value={formatPercent(stats.avg_confidence)} />
            </div>

            {/* Status breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-8">
              {(Object.entries(stats.by_status) as [RecommendationStatus, number][]).map(([status, count]) => (
                <div
                  key={status}
                  className="rounded-[var(--radius-md)] px-4 py-3 text-center"
                  style={{ background: "rgba(20, 20, 20, 0.03)" }}
                >
                  <div className="text-[0.72rem] font-[700] uppercase tracking-[0.1em] mb-1" style={{ color: "var(--brand-muted)" }}>
                    {STATUS_LABELS[status]}
                  </div>
                  <div className="text-[1.16rem] font-[800]">{count}</div>
                </div>
              ))}
            </div>

            <FilterPanel
              activeFilter={filter}
              activeSort={sort}
              searchQuery={search}
              onFilterChange={setFilter}
              onSortChange={setSort}
              onSearchChange={setSearch}
            />

            <div className="mt-6">
              <RankingTable candidates={filtered} />
            </div>
              </>
            ) : null}
          </div>
        </main>
      </div>
    </>
  );
}

function DashboardStateCard({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="card p-12 text-center">
      <h2 className="text-[1.1rem] font-[800] mb-3">{title}</h2>
      <p className="text-[0.9rem] mb-6" style={{ color: "var(--brand-muted)" }}>
        {description}
      </p>
      {action}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: boolean;
}) {
  return (
    <div
      className="card px-5 py-4"
      style={accent ? { background: "linear-gradient(180deg, #c1f11d, #defb75)" } : {}}
    >
      <div
        className="text-[0.72rem] font-[700] uppercase tracking-[0.1em] mb-1"
        style={{ color: accent ? "rgba(20, 20, 20, 0.6)" : "var(--brand-muted)" }}
      >
        {label}
      </div>
      <div className="text-[1.9rem] font-[800]" style={{ lineHeight: 1.1 }}>
        {value}
      </div>
    </div>
  );
}
