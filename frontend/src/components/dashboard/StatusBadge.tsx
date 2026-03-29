import type { RecommendationStatus } from "@/types";

const STATUS_CONFIG: Record<RecommendationStatus, { label: string; className: string }> = {
  STRONG_RECOMMEND: { label: "Рекомендован", className: "badge--lime" },
  RECOMMEND: { label: "К рассмотрению", className: "badge--blue" },
  REVIEW_NEEDED: { label: "Требует проверки", className: "badge--coral" },
  LOW_SIGNAL: { label: "Мало данных", className: "badge--neutral" },
  MANUAL_REVIEW: { label: "Ручная проверка", className: "badge--coral" },
};

interface StatusBadgeProps {
  status: RecommendationStatus;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  return <span className={`badge ${config.className}`}>{config.label}</span>;
}
