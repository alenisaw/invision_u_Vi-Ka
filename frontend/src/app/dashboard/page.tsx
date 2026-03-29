"use client";

import { useState, useMemo } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import FilterPanel from "@/components/dashboard/FilterPanel";
import RankingTable from "@/components/dashboard/RankingTable";
import { MOCK_CANDIDATES, MOCK_STATS } from "@/lib/mock-data";
import { formatPercent } from "@/lib/utils";
import type { RecommendationStatus } from "@/types";

const STATUS_LABELS: Record<RecommendationStatus, string> = {
  STRONG_RECOMMEND: "Настоятельно рекомендованы",
  RECOMMEND: "Рекомендованы",
  REVIEW_NEEDED: "Нужна проверка",
  LOW_SIGNAL: "Мало данных",
  MANUAL_REVIEW: "Ручная проверка",
};

export default function DashboardPage() {
  const [filter, setFilter] = useState<RecommendationStatus | "ALL">("ALL");
  const [sort, setSort] = useState("rpi_desc");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let result = [...MOCK_CANDIDATES];

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
  }, [filter, sort, search]);

  const stats = MOCK_STATS;

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
          </div>
        </main>
      </div>
    </>
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
