"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import { reviewerApi } from "@/lib/api";
import { getRoleLabel } from "@/lib/auth-ui";
import { formatDateTime, getStatusLabel } from "@/lib/i18n";
import type { CommitteeMemberStatus, RecommendationStatus, ReviewerAction } from "@/types";

interface OverridePanelProps {
  candidateId: string;
  currentStatus: RecommendationStatus;
  committeeMembers?: CommitteeMemberStatus[];
  auditLogs?: ReviewerAction[];
  onSuccess?: () => Promise<void> | void;
}

const STATUS_OPTIONS: RecommendationStatus[] = [
  "STRONG_RECOMMEND",
  "RECOMMEND",
  "WAITLIST",
  "DECLINED",
];

export default function OverridePanel({
  candidateId,
  currentStatus,
  committeeMembers = [],
  auditLogs = [],
  onSuccess,
}: OverridePanelProps) {
  const { locale } = useLocale();
  const { user } = useAuth();
  const [newStatus, setNewStatus] = useState<RecommendationStatus>(currentStatus);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [hasError, setHasError] = useState(false);

  const labels = useMemo(
    () =>
      locale === "ru"
        ? {
            reviewerTitle: "Рекомендация члена комиссии",
            reviewerDescription:
              "Укажите рекомендацию по кандидату и коротко обоснуйте принятое решение. Ваше заключение увидит председатель комиссии.",
            chairTitle: "Решение председателя комиссии",
            chairDescription:
              "Ниже показаны статусы по каждому члену комиссии. Председатель комиссии принимает итоговое решение по кандидату на основании рекомендаций и материалов профиля.",
            adminTitle: "Сводка по комиссии",
            adminDescription:
              "Просмотр статусов членов комиссии и итогового решения без права утверждения.",
            recommendation: "Рекомендация",
            rationale: "Обоснование рекомендации",
            rationalePlaceholder:
              "Опишите причины рекомендации в официальной форме: сильные стороны, риски и вывод комиссии.",
            submitReviewer: "Сохранить рекомендацию",
            submitChair: "Утвердить итоговое решение",
            saving: "Сохранение...",
            successReviewer: "Рекомендация члена комиссии сохранена.",
            successChair: "Итоговое решение председателя комиссии сохранено.",
            error: "Не удалось сохранить решение комиссии.",
            committeeTitle: "Статусы членов комиссии",
            committeeMember: "Член комиссии",
            committeeStatus: "Статус ознакомления",
            committeeRecommendation: "Рекомендация",
            committeeReason: "Обоснование",
            committeeActivity: "Последняя активность",
            viewed: "Просмотрел",
            notViewed: "Не просмотрел",
            recommendationPending: "Рекомендация не предоставлена",
            noComment: "Обоснование пока не указано",
            noActivity: "Активность отсутствует",
          }
        : {
            reviewerTitle: "Committee member recommendation",
            reviewerDescription:
              "Record your recommendation for the candidate and provide a concise justification. Your assessment will be visible to the Chair of the Committee.",
            chairTitle: "Chair decision",
            chairDescription:
              "Review the status of each committee member below. The Chair of the Committee records the final decision after reviewing the recommendations and candidate materials.",
            adminTitle: "Committee overview",
            adminDescription:
              "Read-only overview of committee participation and the final candidate outcome.",
            recommendation: "Recommendation",
            rationale: "Recommendation rationale",
            rationalePlaceholder:
              "Summarize the reasoning in a formal tone: strengths, risks, and the committee conclusion.",
            submitReviewer: "Save recommendation",
            submitChair: "Save final decision",
            saving: "Saving...",
            successReviewer: "Committee recommendation saved.",
            successChair: "Final chair decision saved.",
            error: "Failed to save the committee decision.",
            committeeTitle: "Committee member statuses",
            committeeMember: "Committee member",
            committeeStatus: "Review status",
            committeeRecommendation: "Recommendation",
            committeeReason: "Rationale",
            committeeActivity: "Last activity",
            viewed: "Viewed",
            notViewed: "Not viewed",
            recommendationPending: "Recommendation not submitted",
            noComment: "No rationale provided yet",
            noActivity: "No activity",
          },
    [locale],
  );

  useEffect(() => {
    setNewStatus(currentStatus);
  }, [currentStatus]);

  useEffect(() => {
    if (!user || (user.role !== "reviewer" && user.role !== "chair")) {
      return;
    }
    void reviewerApi.recordCandidateViewed(candidateId).catch(() => undefined);
  }, [candidateId, user]);

  async function handleSubmit() {
    if (!user || !comment.trim()) {
      return;
    }

    setSubmitting(true);
    setHasError(false);
    setMessage("");

    try {
      await reviewerApi.submitCommitteeDecision(candidateId, {
        new_status: newStatus,
        comment: comment.trim(),
      });
      setMessage(user.role === "chair" ? labels.successChair : labels.successReviewer);
      await onSuccess?.();
    } catch (err) {
      setHasError(true);
      setMessage(err instanceof Error ? err.message : labels.error);
    } finally {
      setSubmitting(false);
    }
  }

  if (!user) {
    return null;
  }

  const isChair = user.role === "chair";
  const isReviewer = user.role === "reviewer";
  const isAdmin = user.role === "admin";

  return (
    <div className="card p-6">
      <div className="eyebrow mb-4">
        {isChair ? labels.chairTitle : isReviewer ? labels.reviewerTitle : labels.adminTitle}
      </div>
      <p className="text-[0.88rem] mb-5 text-muted leading-relaxed">
        {isChair ? labels.chairDescription : isReviewer ? labels.reviewerDescription : labels.adminDescription}
      </p>

      {(isChair || isAdmin) && (
        <div className="rounded-[1.15rem] border p-4 mb-5 bg-[var(--surface-subtle)]" style={{ borderColor: "var(--brand-line)" }}>
          <div className="text-[0.78rem] font-[800] uppercase tracking-[0.12em] text-muted mb-4">
            {labels.committeeTitle}
          </div>
          <div className="flex flex-col gap-3">
            {committeeMembers.length > 0 ? (
              committeeMembers.map((member) => (
                <CommitteeMemberRow
                  key={member.user_id}
                  member={member}
                  locale={locale}
                  labels={labels}
                />
              ))
            ) : (
              <div className="text-[0.85rem] text-muted">{labels.noActivity}</div>
            )}
          </div>
        </div>
      )}

      {(isReviewer || isChair) && (
        <div className="flex flex-col gap-4">
          <div className="rounded-[1.05rem] px-4 py-3 bg-[var(--surface-subtle)] border border-[var(--brand-line)]">
            <div className="text-[0.76rem] font-[800] uppercase tracking-[0.12em] text-muted mb-1">
              {getRoleLabel(user.role, locale)}
            </div>
            <div className="text-[0.98rem] font-[800]">{user.full_name}</div>
          </div>

          <div>
            <label className="text-[0.82rem] font-[700] block mb-2">{labels.recommendation}</label>
            <select
              value={newStatus}
              onChange={(event) => setNewStatus(event.target.value as RecommendationStatus)}
              className="w-full px-4 pr-10 py-3 text-[0.88rem] font-[600] rounded-[0.8rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] cursor-pointer outline-none focus:ring-2 focus:ring-[var(--brand-blue)] transition-all"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {getStatusLabel(option, locale)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[0.82rem] font-[700] block mb-2">{labels.rationale}</label>
            <textarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder={labels.rationalePlaceholder}
              rows={4}
              className="px-4 py-3 text-[0.88rem] font-[500] resize-y"
            />
          </div>

          {message ? (
            <div
              className={`rounded-[1rem] px-4 py-3 text-[0.84rem] font-[700] ${
                hasError
                  ? "bg-[var(--danger-soft-bg)] text-[var(--danger-soft-text)]"
                  : "bg-[var(--badge-lime-bg)] text-[var(--badge-lime-text)]"
              }`}
            >
              {message}
            </div>
          ) : null}

          <button
            onClick={handleSubmit}
            disabled={submitting || !comment.trim()}
            className="btn btn--dark btn--sm self-end disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {submitting ? labels.saving : isChair ? labels.submitChair : labels.submitReviewer}
          </button>
        </div>
      )}

      {isAdmin && auditLogs.length > 0 && (
        <div className="mt-5 pt-5 border-t border-[var(--brand-line)]">
          <div className="text-[0.78rem] font-[800] uppercase tracking-[0.12em] text-muted mb-3">
            {labels.committeeActivity}
          </div>
          <div className="flex flex-col gap-3">
            {auditLogs.slice(0, 6).map((log) => (
              <div key={log.id} className="rounded-[1rem] border px-4 py-3 bg-[var(--surface-subtle)]" style={{ borderColor: "var(--brand-line)" }}>
                <div className="flex items-center justify-between gap-3 mb-2">
                  <span className="text-[0.84rem] font-[800]">{log.reviewer_id}</span>
                  <span className="text-[0.76rem] text-muted">{formatDateTime(log.created_at, locale)}</span>
                </div>
                <div className="text-[0.82rem] text-muted-strong">
                  {log.new_status ? getStatusLabel(log.new_status, locale) : labels.recommendationPending}
                </div>
                {log.comment ? <div className="text-[0.82rem] text-muted mt-2">{log.comment}</div> : null}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function CommitteeMemberRow({
  member,
  locale,
  labels,
}: {
  member: CommitteeMemberStatus;
  locale: "ru" | "en";
  labels: Record<string, string>;
}) {
  return (
    <div className="rounded-[1rem] border p-4 bg-[var(--surface-soft)]" style={{ borderColor: "var(--brand-line)" }}>
      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.8fr_0.8fr] gap-4">
        <div>
          <div className="text-[0.96rem] font-[800]">{member.full_name}</div>
          <div className="text-[0.76rem] font-[700] text-muted mt-1">
            {labels.committeeMember}
          </div>
        </div>

        <div>
          <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted mb-2">
            {labels.committeeStatus}
          </div>
          <span className={`badge ${member.has_viewed ? "badge--blue" : "badge--neutral"}`}>
            {member.has_viewed ? labels.viewed : labels.notViewed}
          </span>
        </div>

        <div>
          <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted mb-2">
            {labels.committeeActivity}
          </div>
          <div className="text-[0.82rem] text-muted-strong">
            {member.last_activity_at ? formatDateTime(member.last_activity_at, locale) : labels.noActivity}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 lg:grid-cols-[0.8fr_1.2fr] gap-4">
        <div>
          <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted mb-2">
            {labels.committeeRecommendation}
          </div>
          <div className="text-[0.86rem] font-[700]">
            {member.has_recommendation && member.recommendation_status
              ? getStatusLabel(member.recommendation_status, locale)
              : labels.recommendationPending}
          </div>
        </div>

        <div>
          <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted mb-2">
            {labels.committeeReason}
          </div>
          <div className="text-[0.84rem] text-muted leading-relaxed">
            {member.recommendation_comment || labels.noComment}
          </div>
        </div>
      </div>
    </div>
  );
}
