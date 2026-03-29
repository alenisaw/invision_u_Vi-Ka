import type { RecommendationStatus } from "@/types";

const STATUS_CONFIG: Record<RecommendationStatus, { label: string; className: string }> = {
  STRONG_RECOMMEND: { label: "Сильная рекомендация", className: "badge--lime" },
  RECOMMEND: { label: "Рекомендован", className: "badge--blue" },
  WAITLIST: { label: "Лист ожидания", className: "badge--coral" },
  DECLINED: { label: "Отклонен", className: "badge--neutral" },
};

interface StatusBadgeProps {
  status: RecommendationStatus;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  return <span className={`badge ${config.className}`}>{config.label}</span>;
}
