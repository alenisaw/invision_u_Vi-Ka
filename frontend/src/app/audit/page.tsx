"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import { reviewerApi } from "@/lib/api";
import { formatDateTime, getStatusLabel } from "@/lib/i18n";
import type { AuditFeedItem } from "@/types";

const ACTION_STYLES: Record<string, { bg: string; color: string }> = {
  viewed: { bg: "rgba(61, 237, 241, 0.18)", color: "#0a6a6d" },
  recommendation: { bg: "rgba(193, 241, 29, 0.28)", color: "#415005" },
  chair_decision: { bg: "rgba(255, 142, 112, 0.18)", color: "#ac472e" },
};

const ACTION_LABEL_KEYS: Record<string, string> = {
  viewed: "audit.actionViewed",
  recommendation: "audit.actionRecommendation",
  chair_decision: "audit.actionChairDecision",
};

export default function AuditPage() {
  const router = useRouter();
  const { locale, t } = useLocale();
  const { user, loading: authLoading } = useAuth();
  const [actions, setActions] = useState<AuditFeedItem[]>([]);
  const [candidateNames, setCandidateNames] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.replace("/login");
      return;
    }
    if (user?.role === "admin") {
      void loadAudit();
    }
  }, [authLoading, router, user]);

  async function loadAudit() {
    setLoading(true);
    setError("");

    try {
      const [nextActions, candidates] = await Promise.all([
        reviewerApi.listAuditFeed(),
        reviewerApi.listDashboardCandidates(),
      ]);
      setActions(nextActions);
      setCandidateNames(
        Object.fromEntries(candidates.map((candidate) => [candidate.candidate_id, candidate.name])),
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : t("audit.loadError"),
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header />
      <main className="p-6 lg:p-8">
        <div className="container-app">
            <h1
              className="text-[clamp(2rem,1.65rem+1.8vw,3.2rem)] font-[800] mb-8"
              style={{ letterSpacing: "-0.04em" }}
            >
              {t("audit.title")}
            </h1>

            {loading ? (
              <div className="card p-12 text-center">
                <p className="text-[1rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
                  {t("audit.loading")}
                </p>
              </div>
            ) : error ? (
              <div className="card p-12 text-center">
                <p className="text-[1rem] font-[600] mb-4">{error}</p>
                <button onClick={() => void loadAudit()} className="btn btn--dark btn--sm">
                  {t("common.retry")}
                </button>
              </div>
            ) : (
            <div className="card overflow-hidden" style={{ borderRadius: "1rem" }}>
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(20, 20, 20, 0.07)" }}>
                    <th className="eyebrow px-5 py-4 text-left">{t("audit.time")}</th>
                    <th className="eyebrow px-5 py-4 text-left">{t("audit.reviewer")}</th>
                    <th className="eyebrow px-5 py-4 text-left">{t("audit.candidate")}</th>
                    <th className="eyebrow px-5 py-4 text-left">{t("audit.action")}</th>
                    <th className="eyebrow px-5 py-4 text-left">{t("audit.statusChange")}</th>
                    <th className="eyebrow px-5 py-4 text-left">{t("audit.comment")}</th>
                  </tr>
                </thead>
                <tbody>
                  {actions.map((action) => {
                    const candidateName = action.candidate_id
                      ? candidateNames[action.candidate_id]
                      : undefined;
                    const style = ACTION_STYLES[action.action_type] ?? ACTION_STYLES.viewed;

                    return (
                      <tr
                        key={action.id}
                        style={{ borderBottom: "1px solid rgba(20, 20, 20, 0.05)" }}
                      >
                        <td className="px-5 py-4">
                          <span className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>
                            {formatDateTime(action.created_at, locale)}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-[0.88rem] font-[700]">
                            {action.reviewer_name ?? action.actor}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-[0.88rem] font-[800]">
                            {candidateName ?? action.candidate_id?.slice(0, 8) ?? t("common.none")}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <span
                            className="badge text-[0.72rem]"
                            style={{ background: style.bg, color: style.color }}
                          >
                            {t(ACTION_LABEL_KEYS[action.action_type] ?? "audit.action")}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          {action.previous_status && action.new_status && action.previous_status !== action.new_status ? (
                            <span className="text-[0.82rem]">
                              <span style={{ color: "var(--brand-muted)" }}>{getStatusLabel(action.previous_status, locale)}</span>
                              {" → "}
                              <span className="font-[700]">{getStatusLabel(action.new_status, locale)}</span>
                            </span>
                          ) : (
                            <span className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>{t("common.none")}</span>
                          )}
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-[0.82rem]" style={{ color: "var(--brand-muted-strong)" }}>
                            {action.comment ?? t("common.none")}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            )}
        </div>
      </main>
    </>
  );
}
