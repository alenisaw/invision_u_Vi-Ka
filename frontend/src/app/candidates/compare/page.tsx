"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import CompareRadar from "@/components/candidate/CompareRadar";
import PipelineProgress from "@/components/candidate/PipelineProgress";
import { demoApi } from "@/lib/api";
import { SUB_SCORE_LABELS, formatPercent } from "@/lib/utils";
import type { PipelineResult } from "@/types";

const STATUS_STYLES: Record<string, { bg: string; color: string }> = {
  STRONG_RECOMMEND: { bg: "rgba(193, 241, 29, 0.18)", color: "#415005" },
  RECOMMEND:        { bg: "rgba(61, 237, 241, 0.16)", color: "#0a6a6d" },
  WAITLIST:         { bg: "rgba(255, 200, 60, 0.18)", color: "#7a5d00" },
  DECLINED:         { bg: "rgba(255, 142, 112, 0.14)", color: "#ac472e" },
};

interface SlugState {
  slug: string;
  status: "pending" | "running" | "done" | "error";
  step: number;
  result: PipelineResult | null;
  error: string | null;
}

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Загрузка...</div>}>
      <ComparePageInner />
    </Suspense>
  );
}

function ComparePageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const slugsParam = searchParams.get("slugs") ?? "";
  const slugs = slugsParam.split(",").filter(Boolean);

  const [states, setStates] = useState<SlugState[]>([]);

  useEffect(() => {
    if (slugs.length < 2) {
      router.replace("/candidates");
      return;
    }
    setStates(slugs.map((slug) => ({ slug, status: "pending", step: 0, result: null, error: null })));
  }, [slugsParam]);

  useEffect(() => {
    if (states.length === 0 || states.some((s) => s.status !== "pending")) return;

    async function runAll() {
      for (let i = 0; i < states.length; i++) {
        setStates((prev) =>
          prev.map((s, j) => (j === i ? { ...s, status: "running" } : s)),
        );

        const stepInterval = setInterval(() => {
          setStates((prev) =>
            prev.map((s, j) =>
              j === i && s.step < 6 ? { ...s, step: s.step + 1 } : s,
            ),
          );
        }, 1500);

        try {
          const result = await demoApi.runFixture(states[i].slug);
          clearInterval(stepInterval);
          setStates((prev) =>
            prev.map((s, j) =>
              j === i ? { ...s, status: "done", step: 7, result } : s,
            ),
          );
        } catch (err) {
          clearInterval(stepInterval);
          setStates((prev) =>
            prev.map((s, j) =>
              j === i
                ? { ...s, status: "error", error: err instanceof Error ? err.message : "Error" }
                : s,
            ),
          );
        }
      }
    }

    runAll();
  }, [states.length]);

  const allDone = states.length > 0 && states.every((s) => s.status === "done");
  const completedResults = states.filter((s) => s.result).map((s) => s.result!);

  const subScoreKeys = completedResults[0]
    ? Object.keys(completedResults[0].score.sub_scores)
    : [];

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8">
          <div className="container-app">
            <div className="flex items-center gap-4 mb-6">
              <Link href="/candidates" className="text-[0.88rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
                &larr; Назад
              </Link>
              <h1
                className="text-[clamp(1.6rem,1.4rem+1vw,2.4rem)] font-[800]"
                style={{ letterSpacing: "-0.03em" }}
              >
                Сравнение кандидатов
              </h1>
            </div>

            {/* Pipeline progress for each candidate */}
            {!allDone && (
              <div className="flex flex-col gap-4 mb-8">
                {states.map((s) => (
                  <div key={s.slug} className="card p-4">
                    <div className="text-[0.85rem] font-[700] mb-2">{s.slug}</div>
                    <PipelineProgress
                      status={
                        s.status === "pending"
                          ? "idle"
                          : s.status === "running"
                            ? "running"
                            : s.status === "done"
                              ? "completed"
                              : "error"
                      }
                      currentStep={s.step}
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Results */}
            {allDone && (
              <>
                {/* Radar */}
                <CompareRadar
                  candidates={completedResults.map((r, i) => ({
                    name: states[i].slug.replace(/-/g, " "),
                    subScores: r.score.sub_scores,
                  }))}
                />

                {/* Status badges */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 my-6">
                  {completedResults.map((r, i) => {
                    const st = STATUS_STYLES[r.score.recommendation_status] ?? STATUS_STYLES.WAITLIST;
                    return (
                      <div key={states[i].slug} className="card p-4 text-center">
                        <div className="text-[0.85rem] font-[700] mb-2 truncate">
                          {states[i].slug.replace(/-/g, " ")}
                        </div>
                        <span
                          className="inline-block px-3 py-1 rounded-full text-[0.78rem] font-[800] uppercase"
                          style={{ background: st.bg, color: st.color }}
                        >
                          {r.score.recommendation_status.replace(/_/g, " ")}
                        </span>
                        <div className="mt-2 text-[1.2rem] font-[800]">
                          {formatPercent(r.score.review_priority_index)}
                        </div>
                        <div className="text-[0.76rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
                          RPI
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Sub-scores table */}
                <div className="card p-5 overflow-x-auto">
                  <div className="eyebrow mb-4">Детальное сравнение</div>
                  <table className="w-full text-[0.84rem]">
                    <thead>
                      <tr>
                        <th className="text-left font-[700] py-2 pr-4" style={{ color: "var(--brand-muted)" }}>
                          Параметр
                        </th>
                        {states.map((s) => (
                          <th key={s.slug} className="text-center font-[700] py-2 px-3">
                            {s.slug.split("-").slice(0, 1).join(" ")}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {subScoreKeys.map((key) => (
                        <tr key={key} style={{ borderTop: "1px solid rgba(20,20,20,0.06)" }}>
                          <td className="py-2 pr-4 font-[600]" style={{ color: "var(--brand-muted-strong)" }}>
                            {SUB_SCORE_LABELS[key] ?? key}
                          </td>
                          {completedResults.map((r, i) => (
                            <td key={states[i].slug} className="text-center py-2 px-3 font-[700]">
                              {formatPercent(r.score.sub_scores[key] ?? 0)}
                            </td>
                          ))}
                        </tr>
                      ))}
                      <tr style={{ borderTop: "2px solid rgba(20,20,20,0.12)" }}>
                        <td className="py-2 pr-4 font-[800]">Уверенность</td>
                        {completedResults.map((r, i) => (
                          <td key={states[i].slug} className="text-center py-2 px-3 font-[800]">
                            {formatPercent(r.score.confidence)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Links to detail pages */}
                <div className="flex flex-wrap gap-3 mt-6">
                  {completedResults.map((r, i) => (
                    <Link
                      key={states[i].slug}
                      href={`/dashboard/${r.candidate_id}`}
                      className="btn btn--dark btn--sm"
                    >
                      Карточка: {states[i].slug.split("-")[0]}
                    </Link>
                  ))}
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
