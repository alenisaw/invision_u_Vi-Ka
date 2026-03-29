"use client";

import { useState } from "react";
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
}

export default function OverridePanel({ candidateId, currentStatus }: OverridePanelProps) {
  const [newStatus, setNewStatus] = useState<RecommendationStatus>(currentStatus);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit() {
    // TODO: connect to POST /api/v1/dashboard/candidates/{id}/override
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
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
            className="w-full px-4 py-3 rounded-[1rem] text-[0.88rem] font-[500] outline-none resize-none"
            style={{
              border: "1px solid rgba(20, 20, 20, 0.1)",
              background: "rgba(255, 255, 255, 0.82)",
            }}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={!comment.trim() || newStatus === currentStatus}
          className="btn btn--dark btn--sm self-end"
          style={{
            opacity: !comment.trim() || newStatus === currentStatus ? 0.4 : 1,
            cursor: !comment.trim() || newStatus === currentStatus ? "not-allowed" : "pointer",
          }}
        >
          {submitted ? "Отправлено" : "Отправить"}
        </button>
      </div>
    </div>
  );
}
