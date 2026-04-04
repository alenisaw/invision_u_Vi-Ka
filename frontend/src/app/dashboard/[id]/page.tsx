"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import CandidateCard from "@/components/candidate/CandidateCard";
import ExplanationBlock from "@/components/candidate/ExplanationBlock";
import OverridePanel from "@/components/candidate/OverridePanel";
import ScoreRadar from "@/components/candidate/ScoreRadar";
import Header from "@/components/layout/Header";
import { useLocale } from "@/components/providers/LocaleProvider";
import { ApiError, reviewerApi } from "@/lib/api";
import { formatDateTime, getStatusLabel, localizeProgramName } from "@/lib/i18n";
import type {
  CandidateDetail,
  LocalizedTextContent,
  RawCandidateContent,
  ReviewerAction,
} from "@/types";

const RU_INTERFACE = "\u041d\u0430 \u044f\u0437\u044b\u043a\u0435 \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u0430";
const RU_ORIGINAL = "\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b";
const RU_NOT_AVAILABLE =
  "\u041c\u0430\u0442\u0435\u0440\u0438\u0430\u043b \u043f\u043e\u043a\u0430 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d";

export default function CandidateDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { locale, t } = useLocale();
  const [detail, setDetail] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    void loadDetail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id, locale]);

  async function loadDetail() {
    setLoading(true);
    setError("");
    setNotFound(false);

    try {
      const data = await reviewerApi.getCandidateDetail(params.id, locale);
      setDetail(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setNotFound(true);
        setDetail(null);
      } else {
        setError(err instanceof Error ? err.message : t("candidateDetail.loadErrorCard"));
      }
    } finally {
      setLoading(false);
    }
  }

  const copy = useMemo(
    () => ({
      loadingTitle: t("candidateDetail.loadingTitle"),
      loadingDescription: t("candidateDetail.loadingDescription"),
      notFoundTitle: t("candidateDetail.notFoundTitle"),
      loadErrorTitle: t("candidateDetail.loadErrorTitle"),
      loadErrorDescription: t("candidateDetail.loadErrorDescription"),
      backToRanking: t("candidateDetail.backToRanking"),
      rawTitle: t("candidateDetail.rawTitle"),
      essay: t("candidateDetail.essay"),
      transcript: t("candidateDetail.transcript"),
      history: t("candidateDetail.history"),
      unknownComment: t("candidateDetail.unknownComment"),
      interfaceLanguage: locale === "ru" ? RU_INTERFACE : "Interface language",
      original: locale === "ru" ? RU_ORIGINAL : "Original",
      notAvailable: locale === "ru" ? RU_NOT_AVAILABLE : "Material is not available yet",
    }),
    [locale, t],
  );

  if (loading && !detail) {
    return <StateLayout title={copy.loadingTitle} description={copy.loadingDescription} />;
  }

  if (notFound) {
    return (
      <StateLayout
        title={copy.notFoundTitle}
        description={`ID: ${params.id}`}
        action={
          <Link href="/dashboard" className="btn btn--dark btn--sm">
            {copy.backToRanking}
          </Link>
        }
      />
    );
  }

  if (error || !detail) {
    return (
      <StateLayout
        title={copy.loadErrorTitle}
        description={error || copy.loadErrorDescription}
        action={
          <div className="flex items-center justify-center gap-3">
            <button onClick={() => void loadDetail()} className="btn btn--dark btn--sm">
              {t("common.retry")}
            </button>
            <Link href="/dashboard" className="btn btn--ghost btn--sm">
              {copy.backToRanking}
            </Link>
          </div>
        }
      />
    );
  }

  return (
    <>
      <Header />
      <main className="p-6 lg:p-8">
        <div className="container-app">
          <div className="mb-6 flex items-center gap-4">
            <Link href="/dashboard" className="btn btn--ghost btn--sm" style={{ minWidth: 0 }}>
              &larr; {t("common.back")}
            </Link>
            <div>
              <h1
                className="text-[clamp(1.4rem,1.2rem+1vw,2rem)] font-[800]"
                style={{ letterSpacing: "-0.03em" }}
              >
                {detail.name}
              </h1>
              <p className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>
                {localizeProgramName(detail.score.selected_program, locale)}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.25fr_0.75fr]">
            <div className="flex flex-col gap-6">
              <CandidateCard score={detail.score} />
              <ExplanationBlock
                explanation={detail.explanation}
                insertAfterConclusion={
                  detail.raw_content ? (
                    <RawContentSection content={detail.raw_content} copy={copy} />
                  ) : undefined
                }
              />
            </div>

            <div className="flex flex-col gap-6">
              <ScoreRadar subScores={detail.score.sub_scores} />
              <OverridePanel
                candidateId={detail.score.candidate_id}
                currentStatus={detail.score.recommendation_status}
                committeeMembers={detail.committee_members ?? []}
                committeeResolution={detail.committee_resolution ?? null}
                auditLogs={detail.audit_logs ?? []}
                onSuccess={loadDetail}
              />
              <DecisionHistory logs={detail.audit_logs ?? []} locale={locale} copy={copy} />
            </div>
          </div>
        </div>
      </main>
    </>
  );
}

function StateLayout({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <>
      <Header />
      <main className="p-8">
        <div className="container-app">
          <div className="card p-12 text-center">
            <h2 className="mb-3 text-[1.22rem] font-[800]">{title}</h2>
            <p className="mb-6 text-[0.88rem]" style={{ color: "var(--brand-muted)" }}>
              {description}
            </p>
            {action}
          </div>
        </div>
      </main>
    </>
  );
}

function RawContentSection({
  content,
  copy,
}: {
  content: RawCandidateContent;
  copy: Record<string, string>;
}) {
  const hasAny = Boolean(content.essay || content.video_transcript);

  if (!hasAny) {
    return null;
  }

  return (
    <div className="card p-6">
      <div className="mb-5 text-[1rem] font-[800] text-[var(--brand-ink)]">{copy.rawTitle}</div>
      <div className="flex flex-col gap-6">
        {content.essay ? <ContentBlock title={copy.essay} content={content.essay} copy={copy} /> : null}
        {content.video_transcript ? (
          <ContentBlock
            title={copy.transcript}
            content={content.video_transcript}
            copy={copy}
            preserveWhitespace
          />
        ) : null}
      </div>
    </div>
  );
}

function ContentBlock({
  title,
  content,
  copy,
  preserveWhitespace = false,
}: {
  title: string;
  content: LocalizedTextContent;
  copy: Record<string, string>;
  preserveWhitespace?: boolean;
}) {
  const { locale } = useLocale();
  const hasLocalizedView = Boolean(
    content.interface_text &&
      content.interface_locale &&
      content.original_locale &&
      content.interface_locale !== content.original_locale,
  );
  const [viewMode, setViewMode] = useState<"interface" | "original">(
    hasLocalizedView ? "interface" : "original",
  );

  useEffect(() => {
    setViewMode(hasLocalizedView ? "interface" : "original");
  }, [hasLocalizedView, locale]);

  const text =
    viewMode === "interface" && hasLocalizedView
      ? content.interface_text ?? content.original_text
      : content.original_text;
  const displayText = (text || content.original_text || content.interface_text || "").trim();

  if (!displayText) {
    return null;
  }

  return (
    <div className="rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-5 py-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
          {title}
        </div>
        {hasLocalizedView ? (
          <div className="flex rounded-full border border-[var(--brand-line)] bg-[var(--surface-soft)] p-1">
            <button
              type="button"
              onClick={() => setViewMode("interface")}
              className={`rounded-full px-3 py-1.5 text-[0.72rem] font-[800] transition-colors ${
                viewMode === "interface"
                  ? "bg-[var(--brand-ink)] text-[var(--brand-paper)]"
                  : "text-muted-strong"
              }`}
            >
              {copy.interfaceLanguage}
            </button>
            <button
              type="button"
              onClick={() => setViewMode("original")}
              className={`rounded-full px-3 py-1.5 text-[0.72rem] font-[800] transition-colors ${
                viewMode === "original"
                  ? "bg-[var(--brand-ink)] text-[var(--brand-paper)]"
                  : "text-muted-strong"
              }`}
            >
              {copy.original}
            </button>
          </div>
        ) : null}
      </div>

      <div
        className={`text-[0.9rem] font-[500] leading-[1.8] text-[var(--brand-ink)] ${
          preserveWhitespace ? "whitespace-pre-wrap" : ""
        }`}
      >
        {displayText || copy.notAvailable}
      </div>
    </div>
  );
}

function DecisionHistory({
  logs,
  locale,
  copy,
}: {
  logs: ReviewerAction[];
  locale: "ru" | "en";
  copy: Record<string, string>;
}) {
  if (!logs.length) {
    return null;
  }

  return (
    <div className="card p-6">
      <div className="eyebrow mb-4">{copy.history}</div>
      <div className="flex flex-col gap-4">
        {logs.map((log) => (
          <div
            key={log.id}
            className="border-b border-[var(--brand-line)] pb-4 last:border-0 last:pb-0"
          >
            <div className="mb-2 flex items-start justify-between">
              <span className="text-[0.75rem] font-[800] uppercase tracking-wider text-muted-strong">
                {log.reviewer_name}
              </span>
              <span className="font-numbers text-[0.7rem] font-[600] text-muted">
                {formatDateTime(log.created_at, locale)}
              </span>
            </div>

            <div className="mb-2 flex items-center gap-2 text-[0.8rem] font-[700]">
              <span className="text-muted line-through">
                {getStatusLabel(log.previous_status, locale)}
              </span>
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-muted"
              >
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
              <span className={STATUS_COLORS[log.new_status] ?? "text-[var(--brand-paper)]"}>
                {getStatusLabel(log.new_status, locale)}
              </span>
            </div>

            <div className="rounded-[0.5rem] bg-[var(--surface-subtle)] p-3 text-[0.85rem] italic text-muted">
              "{log.comment || copy.unknownComment}"
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  STRONG_RECOMMEND: "text-[var(--brand-lime)]",
  RECOMMEND: "text-[var(--brand-blue)]",
  WAITLIST: "text-[var(--brand-coral)]",
  DECLINED: "text-[var(--danger-soft-text)]",
};
