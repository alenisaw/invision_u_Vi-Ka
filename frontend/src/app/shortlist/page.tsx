"use client";

import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import StatusBadge from "@/components/dashboard/StatusBadge";
import { MOCK_CANDIDATES } from "@/lib/mock-data";
import { formatPercent, formatDate } from "@/lib/utils";

export default function ShortlistPage() {
  const shortlisted = MOCK_CANDIDATES.filter((c) => c.shortlist_eligible).sort(
    (a, b) => b.review_priority_index - a.review_priority_index
  );

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8">
          <div className="container-app">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1
                  className="text-[clamp(2rem,1.65rem+1.8vw,3.2rem)] font-[800]"
                  style={{ letterSpacing: "-0.04em" }}
                >
                  Шорт-лист
                </h1>
                <p className="text-[0.95rem]" style={{ color: "var(--brand-muted)" }}>
                  {shortlisted.length} кандидатов в шорт-листе
                </p>
              </div>
              <button className="btn btn--dark btn--sm">
                Экспорт CSV
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {shortlisted.map((candidate) => (
                <Link
                  key={candidate.candidate_id}
                  href={`/dashboard/${candidate.candidate_id}`}
                  className="card p-5 transition-transform duration-200 hover:-translate-y-0.5"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="text-[0.95rem] font-[800]">{candidate.name}</div>
                      <div className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>
                        Ранг #{candidate.ranking_position}
                      </div>
                    </div>
                    <StatusBadge status={candidate.recommendation_status} />
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <div className="text-[0.72rem] font-[700] uppercase tracking-[0.1em]" style={{ color: "var(--brand-muted)" }}>
                        Балл RPI
                      </div>
                      <div className="text-[1.16rem] font-[800]">
                        {formatPercent(candidate.review_priority_index)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[0.72rem] font-[700] uppercase tracking-[0.1em]" style={{ color: "var(--brand-muted)" }}>
                        Уверенность
                      </div>
                      <div className="text-[1.16rem] font-[800]">
                        {formatPercent(candidate.confidence)}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-1 mb-3">
                    {candidate.top_strengths.map((s) => (
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
                  </div>

                  <div className="text-[0.78rem]" style={{ color: "var(--brand-muted)" }}>
                    {formatDate(candidate.created_at)}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
