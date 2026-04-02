"use client";

import type { RecommendationStatus } from "@/types";

const FILTER_OPTIONS: { value: RecommendationStatus | "ALL"; label: string }[] = [
  { value: "ALL", label: "Все кандидаты" },
  { value: "STRONG_RECOMMEND", label: "Приоритетные" },
  { value: "RECOMMEND", label: "Рекомендуемые" },
  { value: "WAITLIST", label: "Лист ожидания" },
  { value: "DECLINED", label: "Отклоненные" },
];

interface FilterPanelProps {
  activeFilter: RecommendationStatus | "ALL";
  onFilterChange: (filter: RecommendationStatus | "ALL") => void;
}

export default function FilterPanel({
  activeFilter,
  onFilterChange,
}: FilterPanelProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {FILTER_OPTIONS.map((option) => (
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
