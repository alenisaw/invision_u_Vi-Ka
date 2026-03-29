import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatScore(value: number): string {
  return (value * 100).toFixed(0);
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const SUB_SCORE_LABELS: Record<string, string> = {
  leadership_potential: "Лидерство",
  growth_trajectory: "Рост",
  motivation_clarity: "Мотивация",
  initiative_agency: "Инициатива",
  learning_agility: "Обучаемость",
  communication_clarity: "Коммуникация",
  ethical_reasoning: "Этика",
  program_fit: "Соответствие",
};
