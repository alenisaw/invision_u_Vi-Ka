"use client";

import type { RecommendationStatus } from "@/types";

const FILTER_OPTIONS: { value: RecommendationStatus | "ALL"; label: string }[] = [
  { value: "ALL", label: "Все кандидаты" },
  { value: "STRONG_RECOMMEND", label: "Рекомендованы" },
  { value: "RECOMMEND", label: "К рассмотрению" },
  { value: "REVIEW_NEEDED", label: "Требуют проверки" },
  { value: "LOW_SIGNAL", label: "Мало данных" },
  { value: "MANUAL_REVIEW", label: "Ручная проверка" },
];

const SORT_OPTIONS = [
  { value: "rpi_desc", label: "Балл: по убыванию" },
  { value: "rpi_asc", label: "Балл: по возрастанию" },
  { value: "date_desc", label: "Сначала новые" },
  { value: "confidence_desc", label: "По уверенности" },
];

interface FilterPanelProps {
  activeFilter: RecommendationStatus | "ALL";
  activeSort: string;
  searchQuery: string;
  onFilterChange: (filter: RecommendationStatus | "ALL") => void;
  onSortChange: (sort: string) => void;
  onSearchChange: (query: string) => void;
}

export default function FilterPanel({
  activeFilter,
  activeSort,
  searchQuery,
  onFilterChange,
  onSortChange,
  onSearchChange,
}: FilterPanelProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:flex-wrap">
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

      <div className="flex items-center gap-3 sm:ml-auto">
        <input
          type="text"
          placeholder="Поиск кандидатов..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="px-4 py-[0.92rem] text-[0.82rem] font-[700] rounded-[1rem] outline-none"
          style={{
            border: "1px solid rgba(20, 20, 20, 0.1)",
            background: "rgba(255, 255, 255, 0.82)",
          }}
        />

        <select
          value={activeSort}
          onChange={(e) => onSortChange(e.target.value)}
          className="chip cursor-pointer outline-none appearance-none pr-8"
          style={{ backgroundImage: "none" }}
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
