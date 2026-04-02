import { clsx, type ClassValue } from "clsx";
import { formatPercent } from "@/lib/i18n";

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatScore(value: number): string {
  return (value * 100).toFixed(0);
}

export { formatPercent };
