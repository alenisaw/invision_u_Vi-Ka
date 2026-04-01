"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import CandidateCard from "@/components/candidate/CandidateCard";
import ScoreRadar from "@/components/candidate/ScoreRadar";
import ExplanationBlock from "@/components/candidate/ExplanationBlock";
import OverridePanel from "@/components/candidate/OverridePanel";
import { ApiError, reviewerApi } from "@/lib/api";
import { formatDate } from "@/lib/utils"; // Убедись, что импорт formatDate есть
import type { CandidateDetail, RawCandidateContent, RecommendationStatus } from "@/types";

export default function CandidateDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { id } = params;
  const [detail, setDetail] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    void loadDetail();
  }, [id]);

  async function loadDetail() {
    setLoading(true);
    setError("");
    setNotFound(false);

    try {
      setDetail(await reviewerApi.getCandidateDetail(id));
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setNotFound(true);
        setDetail(null);
      } else {
        setError(
          err instanceof Error ? err.message : "Не удалось загрузить карточку кандидата.",
        );
      }
    } finally {
      setLoading(false);
    }
  }

  if (loading && !detail) {
    return (
      <>
        <Header />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-8">
            <div className="container-app">
              <div className="card p-12 text-center">
                <h2 className="text-[1.22rem] font-[800] mb-3">Загружаем профиль кандидата</h2>
                <p className="text-[0.88rem] mb-6" style={{ color: "var(--brand-muted)" }}>
                  Подтягиваем score, explainability и reviewer-данные.
                </p>
              </div>
            </div>
          </main>
        </div>
      </>
    );
  }

  if (notFound) {
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

  if (error || !detail) {
    return (
      <>
        <Header />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-8">
            <div className="container-app">
              <div className="card p-12 text-center">
                <h2 className="text-[1.22rem] font-[800] mb-3">Не удалось загрузить кандидата</h2>
                <p className="text-[0.88rem] mb-6" style={{ color: "var(--brand-muted)" }}>
                  {error || "Попробуйте повторить загрузку чуть позже."}
                </p>
                <div className="flex items-center justify-center gap-3">
                  <button onClick={() => void loadDetail()} className="btn btn--dark btn--sm">
                    Повторить
                  </button>
                  <Link href="/dashboard" className="btn btn--ghost btn--sm">
                    Назад к рейтингу
                  </Link>
                </div>
              </div>
            </div>
          </main>
        </div>
      </>
    );
  }

  const historyLogs = detail.audit_logs ?? [];

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
                  {detail.name}
                </h1>
                <p className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>
                  {detail.score.selected_program}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.25fr_0.75fr] gap-6">
              <div className="flex flex-col gap-6">
                <CandidateCard score={detail.score} />
                <ExplanationBlock
                  explanation={detail.explanation}
                  insertAfterConclusion={detail.raw_content ? <RawContentSection content={detail.raw_content} /> : undefined}
                />
              </div>

              <div className="flex flex-col gap-6">
                <ScoreRadar subScores={detail.score.sub_scores} />
                <OverridePanel
                  candidateId={detail.score.candidate_id}
                  currentStatus={detail.score.recommendation_status}
                  onSuccess={loadDetail}
                />
                
                {/* Компонент истории изменений */}
                <DecisionHistory logs={historyLogs} />
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}


function RawContentSection({ content }: { content: RawCandidateContent }) {
  const [open, setOpen] = useState(false);

  const hasAny = content.essay_text || content.video_transcript || content.project_descriptions.length > 0 || content.experience_summary;
  if (!hasAny) return null;

  return (
    <div className="card p-6">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full"
      >
        <div className="eyebrow">Исходные материалы кандидата</div>
        <span className="text-[0.82rem] font-[700] text-muted">
          {open ? "Свернуть" : "Развернуть"}
        </span>
      </button>

      {open && (
        <div className="flex flex-col gap-6 mt-5">
          {content.essay_text && (
            <div>
              <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] mb-3 text-muted">Эссе</div>
              <div
                className="text-[0.88rem] leading-[1.75] font-[500] p-4 rounded-[1rem] whitespace-pre-wrap"
                style={{ background: "var(--surface-subtle)", border: "1px solid var(--brand-line)" }}
              >
                {content.essay_text}
              </div>
            </div>
          )}

          {content.project_descriptions.length > 0 && (
            <div>
              <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] mb-3 text-muted">Описание проектов</div>
              <div className="flex flex-col gap-2">
                {content.project_descriptions.map((p, i) => (
                  <div
                    key={i}
                    className="text-[0.86rem] font-[500] p-3 rounded-[0.8rem]"
                    style={{ background: "var(--surface-subtle)", border: "1px solid var(--brand-line)" }}
                  >
                    {p}
                  </div>
                ))}
              </div>
            </div>
          )}

          {content.experience_summary && (
            <div>
              <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] mb-3 text-muted">Опыт</div>
              <div
                className="text-[0.88rem] leading-[1.75] font-[500] p-4 rounded-[1rem]"
                style={{ background: "var(--surface-subtle)", border: "1px solid var(--brand-line)" }}
              >
                {content.experience_summary}
              </div>
            </div>
          )}

          {content.video_transcript && (
            <div>
              <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] mb-3 text-muted">Транскрипция видео</div>
              <div
                className="text-[0.88rem] leading-[1.75] font-[500] p-4 rounded-[1rem] whitespace-pre-wrap"
                style={{ background: "var(--surface-subtle)", border: "1px solid var(--brand-line)" }}
              >
                {content.video_transcript}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  STRONG_RECOMMEND: "text-[var(--brand-lime)]",
  RECOMMEND: "text-[var(--brand-blue)]",
  WAITLIST: "text-[var(--brand-coral)]",
  DECLINED: "text-[var(--danger-soft-text)]",
};

function DecisionHistory({ logs }: { logs: any[] }) {
  if (!logs || logs.length === 0) return null;

  return (
    <div className="card p-6">
      <div className="eyebrow mb-4">История решений</div>
      <div className="flex flex-col gap-4">
        {logs.map((log) => (
          <div key={log.id} className="pb-4 border-b border-[var(--brand-line)] last:border-0 last:pb-0">
            <div className="flex justify-between items-start mb-2">
              <span className="text-[0.75rem] font-[800] uppercase tracking-wider text-muted-strong">
                {log.reviewer_id}
              </span>
              <span className="text-[0.7rem] font-[600] text-muted font-numbers">
                {new Date(log.created_at).toLocaleDateString("en-US", { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            
            <div className="flex items-center gap-2 mb-2 text-[0.8rem] font-[700]">
              <span className="text-muted line-through">{log.previous_status}</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-muted">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
              <span className={`${STATUS_COLORS[log.new_status] || "text-[var(--brand-paper)]"}`}>
                {log.new_status}
              </span>
            </div>
            
            <div className="text-[0.85rem] text-muted bg-[var(--surface-subtle)] p-3 rounded-[0.5rem] italic">
              «{log.comment}»
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}