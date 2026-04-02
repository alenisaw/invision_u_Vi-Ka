"use client";

import { useEffect, useState } from "react";
import { reviewerApi } from "@/lib/api";
import type { RecommendationStatus } from "@/types";

const STATUS_OPTIONS: { value: RecommendationStatus; label: string }[] = [
  { value: "STRONG_RECOMMEND", label: "Приоритетные" },
  { value: "RECOMMEND", label: "Рекомендованные" },
  { value: "WAITLIST", label: "В Лист ожидания" },
  { value: "DECLINED", label: "Отклоненные" },
];

interface OverridePanelProps {
  candidateId: string;
  currentStatus: RecommendationStatus;
  onSuccess?: () => Promise<void> | void;
}

export default function OverridePanel({
  candidateId,
  currentStatus,
  onSuccess,
}: OverridePanelProps) {
  const [reviewerId, setReviewerId] = useState("committee-reviewer");
  const [newStatus, setNewStatus] = useState<RecommendationStatus>(currentStatus);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setNewStatus(currentStatus);
  }, [currentStatus]);

  async function handleSubmit() {
    if (!reviewerId.trim() || !comment.trim() || newStatus === currentStatus) {
      return;
    }

    setSubmitting(true);
    setHasError(false);
    setMessage("");

    try {
      await reviewerApi.overrideCandidateDecision(candidateId, {
        reviewer_id: reviewerId.trim(),
        new_status: newStatus,
        comment: comment.trim(),
      });
      setComment("");
      setMessage("Изменение сохранено в журнале и применено к кандидату.");
      await onSuccess?.();
    } catch (err) {
      setHasError(true);
      setMessage(
        err instanceof Error ? err.message : "Не удалось применить override.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card p-6">
      <div className="eyebrow mb-4">Переопределение решения</div>
      <p className="text-[0.82rem] mb-4 text-muted">
        Изменить рекомендацию ИИ для кандидата <code className="text-[0.78rem] font-[700]">{candidateId.slice(0, 8)}...</code>
      </p>

      <div className="flex flex-col gap-4">

        <div>
          <label className="text-[0.82rem] font-[700] block mb-2">ID рецензента</label>
          <input
            type="text"
            value={reviewerId}
            onChange={(e) => setReviewerId(e.target.value)}
            placeholder="committee-reviewer"
            data-testid="reviewer-id-input"
            className="w-full px-4 py-3 text-[0.88rem] font-[500] rounded-[0.8rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] outline-none focus:ring-2 focus:ring-[var(--brand-blue)] transition-all"
          />
        </div>

        <div>
          <label className="text-[0.82rem] font-[700] block mb-2">Новый статус</label>
          <select
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value as RecommendationStatus)}
            data-testid="override-status-select"
            className="w-full px-4 pr-10 py-3 text-[0.88rem] font-[600] rounded-[0.8rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] cursor-pointer outline-none focus:ring-2 focus:ring-[var(--brand-blue)] transition-all"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-[0.82rem] font-[700] block mb-2">Комментарий (обязательно)</label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Укажите причину изменения решения..."
            rows={3}
            data-testid="override-comment-input"
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
          disabled={
            submitting ||
            !reviewerId.trim() ||
            !comment.trim() ||
            newStatus === currentStatus
          }
          data-testid="submit-override-button"
          className="btn btn--dark btn--sm self-end disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {submitting ? "Сохраняем..." : "Отправить"}
        </button>
      </div>
    </div>
  );
}