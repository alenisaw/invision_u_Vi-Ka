"use client";

import { use } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import CandidateCard from "@/components/candidate/CandidateCard";
import ScoreRadar from "@/components/candidate/ScoreRadar";
import ExplanationBlock from "@/components/candidate/ExplanationBlock";
import OverridePanel from "@/components/candidate/OverridePanel";
import { getMockCandidateDetail, MOCK_CANDIDATES } from "@/lib/mock-data";

export default function CandidateDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const detail = getMockCandidateDetail(id);
  const candidateInfo = MOCK_CANDIDATES.find((c) => c.candidate_id === id);

  if (!detail) {
    return (
      <>
        <Header />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-8">
            <div className="container-app">
              <div className="card p-12 text-center">
                <h2 className="text-[1.22rem] font-[800] mb-3">Кандидат не найден</h2>
                <p className="text-[0.88rem] mb-6" style={{ color: "var(--brand-muted)" }}>
                  ID: {id}
                </p>
                <Link href="/dashboard" className="btn btn--dark btn--sm">
                  Назад к рейтингу
                </Link>
              </div>
            </div>
          </main>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8">
          <div className="container-app">
            <div className="flex items-center gap-4 mb-6">
              <Link
                href="/dashboard"
                className="btn btn--ghost btn--sm"
                style={{ minWidth: 0 }}
              >
                &larr; Назад
              </Link>
              <div>
                <h1
                  className="text-[clamp(1.4rem,1.2rem+1vw,2rem)] font-[800]"
                  style={{ letterSpacing: "-0.03em" }}
                >
                  {candidateInfo?.name ?? `Кандидат ${id.slice(0, 8)}`}
                </h1>
                <p className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>
                  {detail.score.selected_program}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.25fr_0.75fr] gap-6">
              <div className="flex flex-col gap-6">
                <CandidateCard score={detail.score} />
                <ExplanationBlock explanation={detail.explanation} />
              </div>

              <div className="flex flex-col gap-6">
                <ScoreRadar subScores={detail.score.sub_scores} />
                <OverridePanel
                  candidateId={detail.score.candidate_id}
                  currentStatus={detail.score.recommendation_status}
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
