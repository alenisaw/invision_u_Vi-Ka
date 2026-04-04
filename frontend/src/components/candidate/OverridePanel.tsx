"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import { reviewerApi } from "@/lib/api";
import { getRoleLabel } from "@/lib/auth-ui";
import { formatDateTime, getStatusLabel } from "@/lib/i18n";
import type {
  CommitteeMemberStatus,
  CommitteeResolutionSummary,
  RecommendationStatus,
  ReviewerAction,
} from "@/types";

interface OverridePanelProps {
  candidateId: string;
  currentStatus: RecommendationStatus;
  committeeMembers?: CommitteeMemberStatus[];
  committeeResolution?: CommitteeResolutionSummary | null;
  auditLogs?: ReviewerAction[];
  onSuccess?: () => Promise<void> | void;
}

const STATUS_OPTIONS: RecommendationStatus[] = [
  "STRONG_RECOMMEND",
  "RECOMMEND",
  "WAITLIST",
  "DECLINED",
];

const RU = {
  summaryTitle: "\u0421\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u0438\u0435 \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438",
  summaryDescription:
    "\u0424\u0438\u043d\u0430\u043b\u044c\u043d\u043e\u0435 \u0440\u0435\u0448\u0435\u043d\u0438\u0435 \u043f\u0440\u0435\u0434\u0441\u0435\u0434\u0430\u0442\u0435\u043b\u044f \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438 \u0438 \u0438\u0442\u043e\u0433\u043e\u0432\u043e\u0435 \u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435 \u043f\u043e \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0443.",
  finalDecisionVisible:
    "\u041f\u043e\u0441\u043b\u0435 \u0443\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f \u0440\u0435\u0448\u0435\u043d\u0438\u0435 \u043f\u0440\u0435\u0434\u0441\u0435\u0434\u0430\u0442\u0435\u043b\u044f \u0432\u0438\u0434\u043d\u043e \u0432\u0441\u0435\u043c \u0447\u043b\u0435\u043d\u0430\u043c \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438.",
  chairOverview: "\u041f\u0440\u0435\u0434\u0441\u0435\u0434\u0430\u0442\u0435\u043b\u044c \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438",
  chairOutcome: "\u0418\u0442\u043e\u0433\u043e\u0432\u043e\u0435 \u0440\u0435\u0448\u0435\u043d\u0438\u0435",
  reviewedMembers: "\u041e\u0437\u043d\u0430\u043a\u043e\u043c\u0438\u043b\u0438\u0441\u044c",
  submittedMembers: "\u041f\u043e\u0434\u0430\u043b\u0438 \u0440\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0430\u0446\u0438\u0438",
  membersTitle: "\u0420\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0430\u0446\u0438\u0438 \u0447\u043b\u0435\u043d\u043e\u0432 \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438",
  finalDecisionComment: "\u041e\u0431\u043e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u0440\u0435\u0434\u0441\u0435\u0434\u0430\u0442\u0435\u043b\u044f",
  finalDecisionSaved:
    "\u041f\u0440\u0435\u0434\u0441\u0435\u0434\u0430\u0442\u0435\u043b\u044c \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438 \u0443\u0436\u0435 \u0437\u0430\u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u043b \u0438\u0442\u043e\u0433\u043e\u0432\u043e\u0435 \u0440\u0435\u0448\u0435\u043d\u0438\u0435.",
};

export default function OverridePanel({
  candidateId,
  currentStatus,
  committeeMembers = [],
  committeeResolution = null,
  auditLogs = [],
  onSuccess,
}: OverridePanelProps) {
  const { locale, t } = useLocale();
  const { user } = useAuth();
  const [newStatus, setNewStatus] = useState<RecommendationStatus>(currentStatus);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [hasError, setHasError] = useState(false);

  const labels = {
    reviewerDescription: t("committee.reviewerDescription"),
    chairDescription: t("committee.chairDescription"),
    adminDescription: t("committee.adminDescription"),
    recommendation: t("committee.recommendation"),
    rationale: t("committee.rationale"),
    rationalePlaceholder: t("committee.rationalePlaceholder"),
    submitReviewer: t("committee.submitReviewer"),
    submitChair: t("committee.submitChair"),
    saving: t("committee.saving"),
    successReviewer: t("committee.successReviewer"),
    successChair: t("committee.successChair"),
    error: t("committee.error"),
    committeeMember: t("committee.member"),
    committeeRecommendation: t("committee.recommendationLabel"),
    committeeReason: t("committee.reason"),
    committeeActivity: t("committee.activity"),
    viewed: t("committee.viewed"),
    notViewed: t("committee.notViewed"),
    recommendationPending: t("committee.recommendationPending"),
    noComment: t("committee.noComment"),
    noActivity: t("committee.noActivity"),
    summaryTitle: locale === "ru" ? RU.summaryTitle : "Committee alignment",
    summaryDescription: locale === "ru" ? RU.summaryDescription : "The final decision from the Chair of the Committee and the candidate outcome.",
    finalDecisionVisible: locale === "ru" ? RU.finalDecisionVisible : "Once approved, the chair decision is visible to all committee members.",
    chairOverview: locale === "ru" ? RU.chairOverview : "Chair of the Committee",
    chairOutcome: locale === "ru" ? RU.chairOutcome : "Final decision",
    reviewedMembers: locale === "ru" ? RU.reviewedMembers : "Viewed by",
    submittedMembers: locale === "ru" ? RU.submittedMembers : "Recommendations submitted",
    membersTitle: locale === "ru" ? RU.membersTitle : "Committee member recommendations",
    finalDecisionComment: locale === "ru" ? RU.finalDecisionComment : "Chair rationale",
    finalDecisionSaved: locale === "ru" ? RU.finalDecisionSaved : "The Chair of the Committee has already recorded the final decision.",
  };

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
  const hasFinalChairDecision = Boolean(committeeResolution);

  return (
    <section className="card p-6 sm:p-7">
      <div className="mb-6 border-b border-[var(--brand-line)] pb-5">
        <div className="eyebrow mb-3">{labels.summaryTitle}</div>
        <p className="max-w-3xl text-[0.95rem] leading-[1.75] text-muted">
          {isChair
            ? labels.chairDescription
            : isReviewer
              ? hasFinalChairDecision
                ? labels.finalDecisionVisible
                : labels.reviewerDescription
              : labels.adminDescription}
        </p>
      </div>

      {committeeResolution ? (
        <div className="mb-7">
          <FinalDecisionCard resolution={committeeResolution} locale={locale} labels={labels} />
        </div>
      ) : null}

      {(isChair || isAdmin) ? (
        <div className="mb-7">
          <ChairOverviewCard
            fullName={isChair ? user.full_name : labels.chairOverview}
            decisionStatus={currentStatus}
            committeeMembers={committeeMembers}
            locale={locale}
            labels={labels}
          />

          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="text-[0.78rem] font-[800] uppercase tracking-[0.12em] text-muted">
              {labels.membersTitle}
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
      ) : null}

      {(isReviewer || isChair) && !hasFinalChairDecision ? (
        <div className="rounded-[1.25rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] p-5 sm:p-6">
          <div className="mb-5 flex flex-col gap-3 rounded-[1rem] border border-[var(--brand-line)] bg-[linear-gradient(180deg,var(--surface-soft),var(--surface-subtle))] px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-[0.72rem] font-[800] uppercase tracking-[0.14em] text-muted">
                {getRoleLabel(user.role, locale)}
              </div>
              <div className="mt-2 text-[1rem] font-[800] leading-[1.3]">{user.full_name}</div>
            </div>
            <StatusPill tone={getRecommendationTone(newStatus, true)}>
              {getStatusLabel(newStatus, locale)}
            </StatusPill>
          </div>

          <div className="grid grid-cols-1 gap-5">
            <div>
              <label className="mb-2 block text-[0.82rem] font-[800] text-muted-strong">
                {labels.recommendation}
              </label>
              <select
                data-testid="committee-status-select"
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
                data-testid="committee-comment-input"
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                placeholder={labels.rationalePlaceholder}
                rows={6}
                className="w-full resize-y rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-elevated)] px-4 py-3 text-[0.9rem] font-[500] leading-[1.7] text-[var(--brand-ink)] outline-none transition-all placeholder:text-muted focus:border-[var(--brand-blue)] focus:ring-2 focus:ring-[var(--brand-blue)]/30"
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
                data-testid="submit-committee-decision-button"
                onClick={handleSubmit}
                disabled={submitting || !comment.trim()}
                className="btn btn--dark btn--sm min-w-[220px] disabled:cursor-not-allowed disabled:opacity-40"
              >
                {submitting ? labels.saving : isChair ? labels.submitChair : labels.submitReviewer}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {isReviewer && hasFinalChairDecision ? (
        <div className="rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-4 py-4 text-[0.9rem] leading-[1.7] text-muted">
          {labels.finalDecisionSaved}
        </div>
      ) : null}

      {isAdmin && auditLogs.length > 0 ? (
        <div className="mt-7 border-t border-[var(--brand-line)] pt-6">
          <div className="mb-4 text-[0.78rem] font-[800] uppercase tracking-[0.12em] text-muted">
            {labels.committeeActivity}
          </div>
          <div className="flex flex-col gap-3">
            {auditLogs.slice(0, 6).map((log) => (
              <div
                key={log.id}
                className="rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-4 py-3"
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className="text-[0.84rem] font-[800]">{log.reviewer_name}</span>
                  <span className="text-[0.76rem] text-muted">
                    {formatDateTime(log.created_at, locale)}
                  </span>
                </div>

                <div className="text-[0.82rem] font-[700] text-muted-strong">
                  {log.new_status
                    ? getStatusLabel(log.new_status, locale)
                    : labels.recommendationPending}
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
      ) : null}
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
      className="rounded-[1.2rem] border p-5 shadow-[0_10px_30px_rgba(0,0,0,0.12)]"
      style={{
        borderColor: "var(--brand-line)",
        background: member.has_recommendation
          ? "linear-gradient(180deg, color-mix(in srgb, var(--badge-blue-bg) 65%, transparent), var(--surface-subtle))"
          : "linear-gradient(180deg,var(--surface-soft),var(--surface-subtle))",
      }}
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

function FinalDecisionCard({
  resolution,
  locale,
  labels,
}: {
  resolution: CommitteeResolutionSummary;
  locale: "ru" | "en";
  labels: Record<string, string>;
}) {
  return (
    <div
      className="rounded-[1.3rem] border p-5 shadow-[0_12px_30px_rgba(0,0,0,0.12)]"
      style={{
        borderColor: "color-mix(in srgb, var(--brand-lime) 22%, var(--brand-line))",
        background:
          "linear-gradient(180deg, color-mix(in srgb, var(--badge-lime-bg) 75%, transparent), color-mix(in srgb, var(--surface-soft) 94%, transparent))",
      }}
    >
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="mb-2 text-[0.74rem] font-[800] uppercase tracking-[0.12em] text-muted">
            {labels.chairOutcome}
          </div>
          <div className="text-[1.02rem] font-[800] leading-[1.3]">{resolution.chair_name}</div>
          <div className="mt-2 text-[0.82rem] text-muted">
            {formatDateTime(resolution.decided_at, locale)}
          </div>
        </div>
        <StatusPill tone={getRecommendationTone(resolution.decision_status, true)}>
          {getStatusLabel(resolution.decision_status, locale)}
        </StatusPill>
      </div>

      {resolution.decision_comment ? (
        <div className="rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-elevated)] p-4">
          <div className="mb-2 text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
            {labels.finalDecisionComment}
          </div>
          <div className="text-[0.88rem] leading-[1.7] text-muted-strong">
            {resolution.decision_comment}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ChairOverviewCard({
  fullName,
  decisionStatus,
  committeeMembers,
  locale,
  labels,
}: {
  fullName: string;
  decisionStatus: RecommendationStatus;
  committeeMembers: CommitteeMemberStatus[];
  locale: "ru" | "en";
  labels: Record<string, string>;
}) {
  const viewedCount = committeeMembers.filter((member) => member.has_viewed).length;
  const submittedCount = committeeMembers.filter((member) => member.has_recommendation).length;

  return (
    <div
      className="mb-5 rounded-[1.3rem] border p-5 shadow-[0_10px_30px_rgba(0,0,0,0.12)]"
      style={{
        borderColor: "color-mix(in srgb, var(--brand-blue) 26%, var(--brand-line))",
        background:
          "linear-gradient(180deg, color-mix(in srgb, var(--badge-blue-bg) 82%, transparent), color-mix(in srgb, var(--surface-soft) 88%, transparent))",
      }}
    >
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="mb-2 text-[0.74rem] font-[800] uppercase tracking-[0.12em] text-muted">
            {labels.chairOverview}
          </div>
          <div className="text-[1.02rem] font-[800] leading-[1.3]">{fullName}</div>
          <div className="mt-2 max-w-[34rem] text-[0.84rem] leading-[1.65] text-muted">
            {locale === "ru"
              ? "\u041f\u0440\u0435\u0434\u0441\u0435\u0434\u0430\u0442\u0435\u043b\u044c \u0432\u0438\u0434\u0438\u0442 \u0441\u0432\u043e\u0434\u043a\u0443 \u043f\u043e \u0443\u0447\u0430\u0441\u0442\u0438\u044e \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438 \u0438 \u043f\u0440\u0438\u043d\u0438\u043c\u0430\u0435\u0442 \u0438\u0442\u043e\u0433\u043e\u0432\u043e\u0435 \u0440\u0435\u0448\u0435\u043d\u0438\u0435 \u043f\u043e \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0443."
              : "The Chair of the Committee reviews participation signals and records the final decision for the candidate."}
          </div>
        </div>
        <StatusPill tone={getRecommendationTone(decisionStatus, true)}>
          {getStatusLabel(decisionStatus, locale)}
        </StatusPill>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <InfoCard
          label={labels.chairOutcome}
          value={getStatusLabel(decisionStatus, locale)}
          tone={getRecommendationTone(decisionStatus, true)}
        />
        <InfoCard
          label={labels.reviewedMembers}
          value={`${viewedCount}/${committeeMembers.length || 0}`}
          renderAsBadge={false}
        />
        <InfoCard
          label={labels.submittedMembers}
          value={`${submittedCount}/${committeeMembers.length || 0}`}
          renderAsBadge={false}
        />
      </div>

      <div className="mt-4 rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-elevated)] p-4">
        <div className="mb-2 text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
          {locale === "ru"
            ? "\u0424\u043e\u043a\u0443\u0441 \u043f\u0440\u0438 \u0441\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u0438\u0438"
            : "Decision focus"}
        </div>
        <div className="text-[0.88rem] leading-[1.7] text-muted-strong">
          {locale === "ru"
            ? "\u0421\u0432\u0435\u0440\u044c\u0442\u0435 \u0438\u0442\u043e\u0433\u043e\u0432\u044b\u0439 \u0441\u0442\u0430\u0442\u0443\u0441 \u0441 \u0440\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0430\u0446\u0438\u044f\u043c\u0438 \u0447\u043b\u0435\u043d\u043e\u0432 \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0438, \u0441\u0438\u0433\u043d\u0430\u043b\u0430\u043c\u0438 \u0440\u0438\u0441\u043a\u0430 \u0438 \u0438\u0441\u0445\u043e\u0434\u043d\u044b\u043c \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u043e\u043c \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0430."
            : "Align the final status with committee recommendations, risk signals, and the candidate source materials."}
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
      className={`inline-flex max-w-full whitespace-normal break-words rounded-full px-3 py-1 text-left text-[0.8rem] font-[800] leading-[1.3] ${className}`}
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
