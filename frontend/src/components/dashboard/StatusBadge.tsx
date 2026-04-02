"use client";

import { useLocale } from "@/components/providers/LocaleProvider";
import { getStatusLabel } from "@/lib/i18n";
import type { RecommendationStatus } from "@/types";

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
  const { locale } = useLocale();
  return <span className={`badge ${STATUS_CLASSES[status]}`}>{getStatusLabel(status, locale)}</span>;
}
