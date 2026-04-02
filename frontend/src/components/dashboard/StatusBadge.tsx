import type { RecommendationStatus } from "@/types";
import { STATUS_LABELS } from "@/lib/utils";

const STATUS_CLASSES: Record<RecommendationStatus, string> = {
  STRONG_RECOMMEND: "badge--lime",
  RECOMMEND: "badge--blue",
  WAITLIST: "badge--coral",
  DECLINED: "badge--neutral",
};

interface StatusBadgeProps {
  status: RecommendationStatus;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`badge ${STATUS_CLASSES[status]}`}>{STATUS_LABELS[status]}</span>;
}
