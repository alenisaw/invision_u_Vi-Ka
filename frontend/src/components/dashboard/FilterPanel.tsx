"use client";

import { useLocale } from "@/components/providers/LocaleProvider";
import { getStatusLabel } from "@/lib/i18n";
import type { RecommendationStatus } from "@/types";

interface FilterPanelProps {
  activeFilter: RecommendationStatus | "ALL";
  onFilterChange: (filter: RecommendationStatus | "ALL") => void;
}

export default function FilterPanel({
  activeFilter,
  onFilterChange,
}: FilterPanelProps) {
  const { locale, t } = useLocale();
  const options: { value: RecommendationStatus | "ALL"; label: string }[] = [
    { value: "ALL", label: t("dashboard.filter.all") },
    { value: "STRONG_RECOMMEND", label: getStatusLabel("STRONG_RECOMMEND", locale) },
    { value: "RECOMMEND", label: getStatusLabel("RECOMMEND", locale) },
    { value: "WAITLIST", label: getStatusLabel("WAITLIST", locale) },
    { value: "DECLINED", label: getStatusLabel("DECLINED", locale) },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onFilterChange(option.value)}
          className={`chip ${activeFilter === option.value ? "is-active" : ""}`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
