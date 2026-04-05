"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import Header from "@/components/layout/Header";
import CompareRadar from "@/components/candidate/CompareRadar";
import { useLocale } from "@/components/providers/LocaleProvider";
import { reviewerApi } from "@/lib/api";
import { formatPercent, getStatusLabel, localizeLabel } from "@/lib/i18n";
import type { CandidateDetail, RecommendationStatus } from "@/types";

const STATUS_CONFIG: Record<RecommendationStatus, { bg: string; text: string }> = {
  STRONG_RECOMMEND: {
    bg: "var(--badge-lime-bg)",
    text: "var(--badge-lime-text)",
  },
  RECOMMEND: {
    bg: "var(--badge-blue-bg)",
    text: "var(--badge-blue-text)",
  },
  WAITLIST: {
    bg: "var(--badge-coral-bg)",
    text: "var(--badge-coral-text)",
  },
  DECLINED: {
    bg: "var(--badge-neutral-bg)",
    text: "var(--badge-neutral-text)",
  },
};

interface CandidateState {
  id: string;
  status: "pending" | "running" | "done" | "error";
  result: CandidateDetail | null;
  error: string | null;
}

export default function ComparePage() {
  const { t } = useLocale();
  return (
    <Suspense fallback={<div className="p-8 text-center text-muted">{t("dashboard.compare.loading")}</div>}>
      <ComparePageInner />
    </Suspense>
  );
}

function ComparePageInner() {
  const { locale, t } = useLocale();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const idsParam = searchParams.get("ids") ?? searchParams.get("slugs") ?? "";
  const ids = idsParam.split(",").filter(Boolean);

  const [states, setStates] = useState<CandidateState[]>([]);

  useEffect(() => {
    if (ids.length < 2) {
      router.replace("/dashboard");
      return;
    }
    setStates(ids.map((id) => ({ id, status: "pending", result: null, error: null })));
  }, [idsParam, router, ids.length]);

  useEffect(() => {
    if (states.length === 0 || states.some((s) => s.status !== "pending")) return;

    async function loadAll() {
      for (let i = 0; i < states.length; i++) {
        setStates((prev) =>
          prev.map((s, j) => (j === i ? { ...s, status: "running" } : s)),
        );

        try {
          const result = await reviewerApi.getCandidateDetail(states[i].id, locale);
          setStates((prev) =>
            prev.map((s, j) =>
              j === i ? { ...s, status: "done", result } : s,
            ),
          );
        } catch (err) {
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

    loadAll();
  }, [states.length, locale]);

  const allDone = states.length > 0 && states.every((s) => s.status === "done");
  const completedResults = states.filter((s) => s.result).map((s) => s.result!);

  const subScoreKeys = completedResults[0]
    ? Object.keys(completedResults[0].score.sub_scores)
    : [];

  return (
    <>
      <Header />
      <main className="p-6 lg:p-8 pb-24">
        <div className="container-app">
            <div className="flex items-center gap-4 mb-8">
              <Link href="/dashboard" className="btn btn--sm btn--ghost min-w-0 px-3">&larr;</Link>
              <h1 className="text-[clamp(1.6rem,1.4rem+1vw,2.4rem)] font-[800] tracking-tight">
                {t("dashboard.compare.title")}
              </h1>
            </div>

            {!allDone && (
              <div className="flex flex-col gap-4 mb-8">
                {states.map((s) => (
                  <div key={s.id} className="card p-5">
                    <div className="text-[0.88rem] font-[700] mb-3 text-muted-strong uppercase tracking-wider">
                      {s.status === "running"
                        ? t("dashboard.compare.running")
                        : s.status === "error"
                          ? t("dashboard.compare.error", { error: s.error ?? "unknown" })
                          : t("dashboard.compare.pending")}
                      {" "}({s.id.slice(0, 8)}...)
                    </div>
                  </div>
                ))}
              </div>
            )}

            {allDone && (
              <div className="flex flex-col gap-8">
                <CompareRadar
                  candidates={completedResults.map((r) => ({
                    name: r.name,
                    subScores: r.score.sub_scores,
                  }))}
                />

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {completedResults.map((r, i) => {
                    const config = STATUS_CONFIG[r.score.recommendation_status] || STATUS_CONFIG.WAITLIST;
                    return (
                      <div key={states[i].id} className="card p-6 text-center flex flex-col justify-center min-h-[180px]">
                        <div className="text-[0.82rem] font-[800] text-muted-strong mb-3">
                          {r.name}
                        </div>
                        <div>
                          <span
                            className="inline-block px-3 py-1 rounded-full text-[0.75rem] font-[800] uppercase tracking-wider"
                            style={{ background: config.bg, color: config.text }}
                          >
                            {getStatusLabel(r.score.recommendation_status, locale)}
                          </span>
                        </div>
                        <div className="mt-5 text-[1.8rem] font-[700] font-numbers leading-none">
                          {formatPercent(r.score.review_priority_index)}
                        </div>
                        <div className="text-[0.72rem] font-[700] text-muted uppercase tracking-widest mt-2">
                          {t("dashboard.rpiScore")}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="card p-6 overflow-hidden">
                  <div className="eyebrow mb-6">{t("dashboard.compare.detail")}</div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-[0.9rem]">
                      <thead>
                        <tr>
                          <th className="text-left font-[700] py-3 pr-4 text-muted border-b border-[var(--brand-line)]">{t("dashboard.compare.parameter")}</th>
                          {completedResults.map((r) => (
                            <th key={r.candidate_id} className="text-center font-[800] py-3 px-4 border-b border-[var(--brand-line)]">
                              {r.name.split(" ")[0]}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {subScoreKeys.map((key) => (
                          <tr key={key} className="border-b border-[var(--brand-line)] last:border-0 hover:bg-[var(--surface-subtle)] transition-colors">
                            <td className="py-4 pr-4 font-[600] text-muted-strong">
                              {localizeLabel(key, locale)}
                            </td>
                            {completedResults.map((r, i) => (
                              <td key={r.candidate_id} className="text-center py-4 px-4 font-[700] font-numbers text-[1.05rem]">
                                {formatPercent(r.score.sub_scores[key] ?? 0)}
                              </td>
                            ))}
                          </tr>
                        ))}
                        <tr className="bg-[var(--brand-ink)] text-[var(--brand-paper)]">
                          <td className="py-4 px-5 font-[800] rounded-l-[0.8rem]">{t("dashboard.compare.aiConfidence")}</td>
                          {completedResults.map((r, i) => (
                            <td key={r.candidate_id} className="text-center py-4 px-4 font-[800] font-numbers text-[1.1rem] last:rounded-r-[0.8rem]">
                              {formatPercent(r.score.confidence)}
                            </td>
                          ))}
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  {completedResults.map((r, i) => (
                    <Link
                      key={states[i].id}
                      href={`/dashboard/${r.candidate_id}`}
                      className="btn btn--dark btn--sm"
                    >
                      {t("dashboard.compare.openCard", { index: i + 1 })}
                    </Link>
                  ))}
                </div>
              </div>
            )}
        </div>
      </main>
    </>
  );
}
