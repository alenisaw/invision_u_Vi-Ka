"use client";

import { useEffect, useState } from "react";
import { reviewerApi } from "@/lib/api";
import type { RecommendationStatus } from "@/types";

const STATUS_OPTIONS: { value: RecommendationStatus; label: string }[] = [
  { value: "STRONG_RECOMMEND", label: "Сильная рекомендация" },
  { value: "RECOMMEND", label: "Рекомендован" },
  { value: "WAITLIST", label: "Лист ожидания" },
  { value: "DECLINED", label: "Отклонен" },
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
  const [newStatus, setNewStatus] = useState<RecommendationStatus>(currentStatus);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setNewStatus(currentStatus);
  }, [currentStatus]);

  async function handleSubmit() {
    if (!comment.trim() || newStatus === currentStatus) {
      return;
    }

    setSubmitting(true);
    setHasError(false);
    setMessage("");

    try {
      await reviewerApi.overrideCandidateDecision(candidateId, {
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
      <p className="text-[0.82rem] mb-4" style={{ color: "var(--brand-muted)" }}>
        Изменить рекомендацию ИИ для кандидата <code className="text-[0.78rem] font-[700]">{candidateId.slice(0, 8)}...</code>
      </p>

      <div className="flex flex-col gap-4">
        <div>
          <label className="text-[0.82rem] font-[700] block mb-2">Новый статус</label>
          <select
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value as RecommendationStatus)}
            data-testid="override-status-select"
            className="w-full px-4 py-3 rounded-[1rem] text-[0.88rem] font-[600] outline-none"
            style={{
              border: "1px solid rgba(20, 20, 20, 0.1)",
              background: "rgba(255, 255, 255, 0.82)",
            }}
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
            className="w-full px-4 py-3 rounded-[1rem] text-[0.88rem] font-[500] outline-none resize-none"
            style={{
              border: "1px solid rgba(20, 20, 20, 0.1)",
              background: "rgba(255, 255, 255, 0.82)",
            }}
          />
        </div>

        {message ? (
          <div
            className="rounded-[var(--radius-md)] px-4 py-3 text-[0.84rem] font-[600]"
            style={{
              background: hasError
                ? "rgba(255, 142, 112, 0.14)"
                : "rgba(193, 241, 29, 0.18)",
              color: hasError ? "#ac472e" : "#415005",
            }}
          >
            {message}
          </div>
        ) : null}

        <button
          onClick={handleSubmit}
          disabled={
            submitting ||
            !comment.trim() ||
            newStatus === currentStatus
          }
          data-testid="submit-override-button"
          className="btn btn--dark btn--sm self-end"
          style={{
            opacity:
              submitting ||
              !comment.trim() ||
              newStatus === currentStatus
                ? 0.4
                : 1,
            cursor:
              submitting ||
              !comment.trim() ||
              newStatus === currentStatus
                ? "not-allowed"
                : "pointer",
          }}
        >
          {submitting ? "Сохраняем..." : "Отправить"}
        </button>
      </div>
    </div>
  );
}
