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
  leadership_potential: "Лидерский потенциал",
  growth_trajectory: "Траектория роста",
  motivation_clarity: "Ясность мотивации",
  initiative_agency: "Инициативность",
  learning_agility: "Обучаемость",
  communication_clarity: "Коммуникация",
  ethical_reasoning: "Этическое мышление",
  program_fit: "Соответствие программе",
};

export const STATUS_LABELS: Record<string, string> = {
  STRONG_RECOMMEND: "Приоритетные",
  RECOMMEND: "Рекомендуемые",
  WAITLIST: "Лист ожидания",
  DECLINED: "Отклоненные",
};

const LOCALIZED_LABELS: Record<string, string> = {
  leadership_potential: "Лидерский потенциал",
  "Leadership Potential": "Лидерский потенциал",
  Leadership: "Лидерский потенциал",
  growth_trajectory: "Траектория роста",
  "Growth Trajectory": "Траектория роста",
  motivation_clarity: "Ясность мотивации",
  "Motivation Clarity": "Ясность мотивации",
  initiative_agency: "Инициативность и ответственность",
  "Initiative and Ownership": "Инициативность и ответственность",
  learning_agility: "Обучаемость",
  "Learning Agility": "Обучаемость",
  communication_clarity: "Ясность коммуникации",
  "Communication Clarity": "Ясность коммуникации",
  ethical_reasoning: "Этическое мышление",
  "Ethical Reasoning": "Этическое мышление",
  program_fit: "Соответствие программе",
  "Program Fit": "Соответствие программе",
  challenges_overcome: "Преодоление сложностей",
  resilience_evidence: "Устойчивость",
  essay_mismatch: "Несоответствие эссе",
  "Essay mismatch": "Несоответствие эссе",
  possible_ai_use: "Риск использования ИИ",
  authenticity_or_ai_risk: "Риск недостоверности или использования ИИ",
  low_cross_source_consistency: "Низкая согласованность источников",
  weak_claim_support: "Слабая доказательная база",
  voice_inconsistency: "Несогласованность речи и текста",
  generic_evidence: "Слишком общие формулировки",
  low_completeness: "Низкая полнота данных",
  no_structured_signals: "Недостаточно структурированных сигналов",
  missing_essay: "Нет текстового эссе",
  missing_video: "Нет видеоинтервью",
  missing_video_transcript: "Нет транскрипции видео",
  missing_project_descriptions: "Нет описаний проектов",
  low_profile_completeness: "Профиль заполнен неполно",
  no_speech_detected: "Речь в видео не распознана",
  low_asr_confidence: "Низкая уверенность ASR",
  asr_processing_failed: "Ошибка обработки видео",
  requires_human_review: "Требуется ручная проверка",
  insufficient_interview_coverage: "Недостаточно данных из интервью",
  short_duration: "Слишком короткое видео",
  unclear_segments_high: "Слишком много неясных фрагментов",
  low_signal_coverage: "Низкое покрытие сигналов",
  low_signal_confidence: "Низкая уверенность сигналов",
  low_confidence: "Низкая общая уверенность",
  missing_or_low_quality_inputs: "Недостаточно качественных входных данных",
  conflicting_signals: "Конфликтующие сигналы",
  narrow_margin_between_classes: "Пограничный результат",
  score_instability_under_perturbation: "Нестабильный результат",
  FAST_TRACK_REVIEW: "Ускоренная проверка",
  STANDARD_REVIEW: "Стандартная проверка",
  REQUIRES_MANUAL_REVIEW: "Ручная проверка",
  essay: "Эссе",
  video_transcript: "Транскрипция видео",
  project_descriptions: "Описания проектов",
  experience_summary: "Описание опыта",
  internal_test_answers: "Ответы внутреннего теста",
};

const SEVERITY_LABELS: Record<string, string> = {
  critical: "Критично",
  warning: "Нужна проверка",
  advisory: "Обратите внимание",
};

function titleCaseEnglish(text: string): string {
  return text
    .split(" ")
    .filter(Boolean)
    .map((part) => part[0]?.toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function prettifyKey(value: string): string {
  return titleCaseEnglish(value.replace(/[_-]+/g, " "));
}

export function localizeLabel(value: string): string {
  return LOCALIZED_LABELS[value] ?? prettifyKey(value);
}

export function localizeLabels(values: string[]): string[] {
  return values.map(localizeLabel);
}

export function localizeSeverity(value: string): string {
  return SEVERITY_LABELS[value.toLowerCase()] ?? localizeLabel(value);
}
