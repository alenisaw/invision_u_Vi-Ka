"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import StatusBadge from "@/components/dashboard/StatusBadge";
import { useLocale } from "@/components/providers/LocaleProvider";
import { reviewerApi } from "@/lib/api";
import { formatDate, formatPercent, localizeLabels } from "@/lib/i18n";
import type { CandidateListItem } from "@/types";

export default function ShortlistPage() {
  const { locale, t } = useLocale();
  const [shortlisted, setShortlisted] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadShortlist();
  }, []);

  async function loadShortlist() {
    setLoading(true);
    setError("");

    try {
      setShortlisted(await reviewerApi.listShortlist());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : t("shortlist.loadError"),
      );
    } finally {
      setLoading(false);
    }
  }

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
                  {t("shortlist.title")}
                </h1>
                <p className="text-[0.95rem]" style={{ color: "var(--brand-muted)" }}>
                  {t("shortlist.count", { count: shortlisted.length })}
                </p>
              </div>
              <button className="btn btn--dark btn--sm">
                {t("shortlist.export")}
              </button>
            </div>

            {loading ? (
              <div className="card p-12 text-center">
                <p className="text-[1rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
                  {t("shortlist.loading")}
                </p>
              </div>
            ) : error ? (
              <div className="card p-12 text-center">
                <p className="text-[1rem] font-[600] mb-4">{error}</p>
                <button onClick={() => void loadShortlist()} className="btn btn--dark btn--sm">
                  {t("common.retry")}
                </button>
              </div>
            ) : shortlisted.length === 0 ? (
              <div className="card p-12 text-center">
                <p className="text-[1rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
                  {t("shortlist.empty")}
                </p>
              </div>
            ) : (
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
                        {t("shortlist.rank", { value: candidate.ranking_position ?? t("common.none") })}
                      </div>
                    </div>
                    <StatusBadge status={candidate.recommendation_status} />
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <div className="text-[0.72rem] font-[700] uppercase tracking-[0.1em]" style={{ color: "var(--brand-muted)" }}>
                        {t("dashboard.rpiScore")}
                      </div>
                      <div className="text-[1.16rem] font-[800]">
                        {formatPercent(candidate.review_priority_index)}
                      </div>
                    </div>
                    <div>
                      <div className="text-[0.72rem] font-[700] uppercase tracking-[0.1em]" style={{ color: "var(--brand-muted)" }}>
                        {t("common.confidence")}
                      </div>
                      <div className="text-[1.16rem] font-[800]">
                        {formatPercent(candidate.confidence)}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-1 mb-3">
                    {localizeLabels(candidate.top_strengths, locale).map((s) => (
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
                    {formatDate(candidate.created_at, locale)}
                  </div>
                </Link>
              ))}
            </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
