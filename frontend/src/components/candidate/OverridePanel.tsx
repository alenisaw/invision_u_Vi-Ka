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
    <section className="card p-6 sm:p-7">
      <div className="mb-6 border-b border-[var(--brand-line)] pb-5">
        <div className="eyebrow mb-3">
          {isChair ? labels.chairTitle : isReviewer ? labels.reviewerTitle : labels.adminTitle}
        </div>
        <p className="max-w-3xl text-[0.95rem] leading-[1.75] text-muted">
          {isChair
            ? labels.chairDescription
            : isReviewer
              ? labels.reviewerDescription
              : labels.adminDescription}
        </p>
      </div>

      {(isChair || isAdmin) && (
        <div className="mb-7">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="text-[0.78rem] font-[800] uppercase tracking-[0.12em] text-muted">
              {labels.committeeTitle}
            </div>
            <div className="rounded-full border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-3 py-1 text-[0.74rem] font-[700] text-muted-strong">
              {committeeMembers.length}
            </div>
          </div>

          {committeeMembers.length > 0 ? (
            <div className="grid grid-cols-1 gap-4">
              {committeeMembers.map((member) => (
                <CommitteeMemberCard
                  key={member.user_id}
                  member={member}
                  locale={locale}
                  labels={labels}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-[1.1rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-4 py-4 text-[0.9rem] text-muted">
              {labels.noActivity}
            </div>
          )}
        </div>
      )}

      {(isReviewer || isChair) && (
        <div className="flex flex-col gap-5">
          <aside className="rounded-[1.25rem] border border-[var(--brand-line)] bg-[linear-gradient(180deg,var(--surface-subtle),var(--surface-soft))] p-5 shadow-[0_12px_28px_rgba(0,0,0,0.08)]">
            <div className="mb-3 text-[0.72rem] font-[800] uppercase tracking-[0.14em] text-muted">
              {getRoleLabel(user.role, locale)}
            </div>
            <div className="mb-2 text-[1.08rem] font-[800] leading-[1.35]">
              {user.full_name}
            </div>
            <div className="mb-5 text-[0.84rem] text-muted">
              {getRoleLabel(user.role, locale)}
            </div>

            <InfoCard
              label={labels.recommendation}
              value={getStatusLabel(newStatus, locale)}
              tone={getRecommendationTone(newStatus, true)}
            />
          </aside>

          <div className="rounded-[1.25rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] p-5 sm:p-6">
            <div className="grid grid-cols-1 gap-5">
              <div>
                <label className="mb-2 block text-[0.82rem] font-[800] text-muted-strong">
                  {labels.recommendation}
                </label>
                <select
                  value={newStatus}
                  onChange={(event) => setNewStatus(event.target.value as RecommendationStatus)}
                  className="w-full rounded-[0.95rem] border border-[var(--brand-line)] bg-[var(--surface-elevated)] px-4 py-3 pr-10 text-[0.9rem] font-[700] text-[var(--brand-ink)] outline-none transition-all focus:border-[var(--brand-blue)] focus:ring-2 focus:ring-[var(--brand-blue)]/30"
                >
                  {STATUS_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {getStatusLabel(option, locale)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-2 block text-[0.82rem] font-[800] text-muted-strong">
                  {labels.rationale}
                </label>
                <textarea
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder={labels.rationalePlaceholder}
                  rows={6}
                  className="w-full rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-elevated)] px-4 py-3 text-[0.9rem] font-[500] leading-[1.7] text-[var(--brand-ink)] outline-none transition-all placeholder:text-muted focus:border-[var(--brand-blue)] focus:ring-2 focus:ring-[var(--brand-blue)]/30 resize-y"
                />
              </div>

              {message ? (
                <div
                  className={`rounded-[1rem] border px-4 py-3 text-[0.84rem] font-[700] ${
                    hasError
                      ? "border-[var(--danger-soft-text)]/20 bg-[var(--danger-soft-bg)] text-[var(--danger-soft-text)]"
                      : "border-[var(--badge-lime-text)]/20 bg-[var(--badge-lime-bg)] text-[var(--badge-lime-text)]"
                  }`}
                >
                  {message}
                </div>
              ) : null}

              <div className="flex justify-end">
                <button
                  onClick={handleSubmit}
                  disabled={submitting || !comment.trim()}
                  className="btn btn--dark btn--sm min-w-[220px] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {submitting ? labels.saving : isChair ? labels.submitChair : labels.submitReviewer}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {isAdmin && auditLogs.length > 0 && (
        <div className="mt-7 border-t border-[var(--brand-line)] pt-6">
          <div className="text-[0.78rem] font-[800] uppercase tracking-[0.12em] text-muted mb-4">
            {labels.committeeActivity}
          </div>
          <div className="flex flex-col gap-3">
            {auditLogs.slice(0, 6).map((log) => (
              <div
                key={log.id}
                className="rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-4 py-3"
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="text-[0.84rem] font-[800]">{log.reviewer_id}</span>
                  <span className="text-[0.76rem] text-muted">{formatDateTime(log.created_at, locale)}</span>
                </div>

                <div className="text-[0.82rem] font-[700] text-muted-strong">
                  {log.new_status ? getStatusLabel(log.new_status, locale) : labels.recommendationPending}
                </div>

                {log.comment ? (
                  <div className="mt-2 text-[0.82rem] leading-[1.65] text-muted">
                    {log.comment}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function CommitteeMemberCard({
  member,
  locale,
  labels,
}: {
  member: CommitteeMemberStatus;
  locale: "ru" | "en";
  labels: Record<string, string>;
}) {
  const recommendationText =
    member.has_recommendation && member.recommendation_status
      ? getStatusLabel(member.recommendation_status, locale)
      : labels.recommendationPending;

  return (
    <div
      className="rounded-[1.2rem] border border-[var(--brand-line)] bg-[linear-gradient(180deg,var(--surface-soft),var(--surface-subtle))] p-5 shadow-[0_10px_30px_rgba(0,0,0,0.12)]"
    >
      <div className="mb-4 flex flex-col items-start gap-3">
        <div>
          <div className="text-[1rem] font-[800] leading-[1.3]">{member.full_name}</div>
          <div className="mt-1 text-[0.78rem] font-[700] uppercase tracking-[0.1em] text-muted">
            {labels.committeeMember}
          </div>
        </div>

        <StatusPill tone={member.has_viewed ? "info" : "neutral"}>
          {member.has_viewed ? labels.viewed : labels.notViewed}
        </StatusPill>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <InfoCard
          label={labels.committeeRecommendation}
          value={recommendationText}
          tone={getRecommendationTone(member.recommendation_status, member.has_recommendation)}
        />
        <InfoCard
          label={labels.committeeActivity}
          value={member.last_activity_at ? formatDateTime(member.last_activity_at, locale) : labels.noActivity}
          renderAsBadge={false}
        />
      </div>

      <div className="mt-4 rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-elevated)] p-4">
        <div className="mb-2 text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
          {labels.committeeReason}
        </div>
        <div className="text-[0.86rem] leading-[1.7] text-muted-strong">
          {member.recommendation_comment || labels.noComment}
        </div>
      </div>
    </div>
  );
}

function InfoCard({
  label,
  value,
  tone = "default",
  renderAsBadge = true,
}: {
  label: string;
  value: string;
  tone?: "default" | "positive" | "warning" | "danger" | "neutral";
  renderAsBadge?: boolean;
}) {
  return (
    <div className="rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-elevated)] p-4">
      <div className="mb-2 text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
        {label}
      </div>
      {renderAsBadge ? (
        <StatusPill tone={tone}>{value}</StatusPill>
      ) : (
        <div className="text-[0.92rem] font-[700] leading-[1.5] text-[var(--brand-ink)]">
          {value}
        </div>
      )}
    </div>
  );
}

function StatusPill({
  children,
  tone = "default",
}: {
  children: string;
  tone?: "default" | "positive" | "warning" | "danger" | "neutral" | "info";
}) {
  const className =
    tone === "positive"
      ? "bg-[var(--badge-lime-bg)] text-[var(--badge-lime-text)]"
      : tone === "warning"
        ? "bg-[rgba(245,158,11,0.14)] text-[rgb(245,158,11)]"
        : tone === "danger"
          ? "bg-[var(--danger-soft-bg)] text-[var(--danger-soft-text)]"
          : tone === "info"
            ? "bg-[var(--badge-blue-bg)] text-[var(--badge-blue-text)]"
            : tone === "neutral"
              ? "bg-[var(--surface-subtle-2)] text-muted-strong"
              : "bg-[var(--surface-subtle)] text-[var(--brand-ink)]";

  return (
    <span
      className={`inline-flex max-w-full rounded-full px-3 py-1 text-left text-[0.8rem] font-[800] leading-[1.3] whitespace-normal break-words ${className}`}
    >
      {children}
    </span>
  );
}

function getRecommendationTone(
  status?: RecommendationStatus | null,
  hasRecommendation?: boolean,
): "positive" | "warning" | "danger" | "neutral" {
  if (!hasRecommendation || !status) {
    return "neutral";
  }

  if (status === "STRONG_RECOMMEND" || status === "RECOMMEND") {
    return "positive";
  }

  if (status === "WAITLIST") {
    return "warning";
  }

  return "danger";
}
