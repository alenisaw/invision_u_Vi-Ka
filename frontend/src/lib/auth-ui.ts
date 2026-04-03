import type { Locale } from "@/lib/i18n";
import type { UserRole } from "@/types";

const ROLE_LABELS: Record<UserRole, { ru: string; en: string }> = {
  admin: {
    ru: "Администратор",
    en: "Administrator",
  },
  chair: {
    ru: "Председатель комиссии",
    en: "Chair of the Committee",
  },
  reviewer: {
    ru: "Член комиссии",
    en: "Committee Member",
  },
};

export function getRoleLabel(role: UserRole, locale: Locale): string {
  return ROLE_LABELS[role][locale];
}

export function getUserInitials(fullName: string): string {
  const parts = fullName
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);

  if (parts.length === 0) {
    return "IU";
  }

  return parts.map((part) => part[0]?.toUpperCase() ?? "").join("");
}
