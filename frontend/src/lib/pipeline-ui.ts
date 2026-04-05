import type { Locale } from "@/lib/i18n";
import { getAiRiskLevel } from "@/lib/i18n";
import type { PipelineQualityStatus } from "@/types";

export type PipelineDisplayStatus = PipelineQualityStatus | "pending";

const AUTHENTICITY_FLAGS = new Set([
  "possible_ai_use",
  "authenticity_or_ai_risk",
  "speech_authenticity_risk",
  "voice_inconsistency",
]);

export function derivePipelineDisplayStatus(flags: string[]): PipelineDisplayStatus {
  const flagSet = new Set(flags);

  if (
    flagSet.has("asr_processing_failed") ||
    flagSet.has("empty_signal_envelope") ||
    flagSet.has("no_structured_signals")
  ) {
    return "degraded";
  }

  if (
    flagSet.has("low_asr_confidence") ||
    flagSet.has("speech_authenticity_risk") ||
    flagSet.has("possible_ai_use") ||
    flagSet.has("authenticity_or_ai_risk") ||
    flagSet.has("low_cross_source_consistency")
  ) {
    return "partial";
  }

  return "healthy";
}

export function getPipelineStatusLabel(status: PipelineDisplayStatus, locale: Locale) {
  if (status === "pending") {
    return locale === "ru" ? "Ожидает обработки" : "Pending processing";
  }
  if (status === "healthy") {
    return locale === "ru" ? "Источник подтвержден" : "Source healthy";
  }
  if (status === "degraded") {
    return locale === "ru" ? "Снижение качества" : "Degraded source";
  }
  if (status === "manual_review_required") {
    return locale === "ru" ? "Нужна ручная проверка" : "Manual review required";
  }
  return locale === "ru" ? "Нужна проверка" : "Needs review";
}

export function getPipelineStatusBadge(status: PipelineDisplayStatus) {
  if (status === "healthy") return "badge--lime";
  if (status === "degraded") return "badge--coral";
  if (status === "manual_review_required" || status === "partial") return "badge--blue";
  return "badge--neutral";
}

export function hasAuthenticityAdvisory(flags: string[]) {
  return flags.some((flag) => AUTHENTICITY_FLAGS.has(flag));
}

export function getAuthenticityAdvisoryLabel(flags: string[], locale: Locale) {
  const level = getAiRiskLevel(flags);
  if (locale === "ru") {
    if (level === "high") return "Аутентичность: высокий риск";
    if (level === "review") return "Аутентичность: проверить";
    return "Аутентичность: ок";
  }
  if (level === "high") return "Authenticity: high risk";
  if (level === "review") return "Authenticity: review";
  return "Authenticity: ok";
}

export function getAuthenticityAdvisoryBadge(flags: string[]) {
  const level = getAiRiskLevel(flags);
  if (level === "high") return "badge--coral";
  if (level === "review") return "badge--blue";
  return "badge--neutral";
}

export function localizePipelineFlag(flag: string, locale: Locale) {
  const labels: Record<string, { ru: string; en: string }> = {
    asr_processing_failed: { ru: "ASR не сработал", en: "ASR failed" },
    low_asr_confidence: { ru: "Низкая уверенность ASR", en: "Low ASR confidence" },
    empty_signal_envelope: { ru: "Пустой набор сигналов", en: "Empty signal envelope" },
    no_structured_signals: { ru: "Нет структурных сигналов", en: "No structured signals" },
    speech_authenticity_risk: {
      ru: "Риск неаутентичной речи",
      en: "Speech authenticity risk",
    },
    possible_ai_use: { ru: "Риск шаблонного текста", en: "Possible AI use" },
    authenticity_or_ai_risk: {
      ru: "Риск неаутентичного нарратива",
      en: "Narrative authenticity risk",
    },
    low_cross_source_consistency: {
      ru: "Низкая согласованность источников",
      en: "Low cross-source consistency",
    },
    weak_claim_support: { ru: "Слабая подтвержденность тезисов", en: "Weak claim support" },
    voice_inconsistency: { ru: "Несогласованность голоса", en: "Voice inconsistency" },
    generic_evidence: { ru: "Слишком общие формулировки", en: "Generic evidence" },
    llm_extraction_fallback_used: {
      ru: "Extraction ушел в fallback",
      en: "Extraction fallback used",
    },
    semantic_similarity_fallback_used: {
      ru: "Semantic fallback",
      en: "Semantic fallback used",
    },
  };

  return labels[flag]?.[locale] ?? flag;
}

export function localizeStageName(stage: string, locale: Locale) {
  const labels: Record<string, { ru: string; en: string }> = {
    gateway: { ru: "Gateway", en: "Gateway" },
    asr: { ru: "ASR", en: "ASR" },
    privacy: { ru: "Privacy", en: "Privacy" },
    profile: { ru: "Profile", en: "Profile" },
    extraction: { ru: "Extraction", en: "Extraction" },
    scoring: { ru: "Scoring", en: "Scoring" },
    explanation: { ru: "Explanation", en: "Explanation" },
  };
  return labels[stage]?.[locale] ?? stage;
}
