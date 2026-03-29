import type {
  CandidateListItem,
  CandidateDetail,
  DashboardStats,
  ReviewerAction,
} from "@/types";

export const MOCK_STATS: DashboardStats = {
  total_candidates: 48,
  shortlisted: 12,
  pending_review: 9,
  processed: 39,
  avg_confidence: 0.79,
  by_status: {
    STRONG_RECOMMEND: 8,
    RECOMMEND: 16,
    REVIEW_NEEDED: 9,
    LOW_SIGNAL: 6,
    MANUAL_REVIEW: 9,
  },
};

export const MOCK_CANDIDATES: CandidateListItem[] = [
  {
    candidate_id: "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
    name: "Алия Нурланова",
    selected_program: "Innovative IT Product Design and Development",
    review_priority_index: 0.91,
    recommendation_status: "STRONG_RECOMMEND",
    confidence: 0.88,
    shortlist_eligible: true,
    ranking_position: 1,
    top_strengths: ["Сильное лидерство", "Высокая траектория роста"],
    caution_flags: [],
    created_at: "2026-03-28T10:30:00Z",
  },
  {
    candidate_id: "d2b3c4d5-e6f7-8901-bcde-f12345678901",
    name: "Дмитрий Ким",
    selected_program: "Innovative IT Product Design and Development",
    review_priority_index: 0.85,
    recommendation_status: "STRONG_RECOMMEND",
    confidence: 0.82,
    shortlist_eligible: true,
    ranking_position: 2,
    top_strengths: ["Исключительная инициатива", "Чёткая мотивация"],
    caution_flags: [],
    created_at: "2026-03-28T11:15:00Z",
  },
  {
    candidate_id: "e3c4d5e6-f7a8-9012-cdef-123456789012",
    name: "Айгерим Сатпаева",
    selected_program: "Innovative IT Product Design and Development",
    review_priority_index: 0.78,
    recommendation_status: "STRONG_RECOMMEND",
    confidence: 0.85,
    shortlist_eligible: true,
    ranking_position: 3,
    top_strengths: ["Обучаемость", "Сильная коммуникация"],
    caution_flags: [],
    created_at: "2026-03-28T09:45:00Z",
  },
  {
    candidate_id: "f4d5e6f7-a8b9-0123-defa-234567890123",
    name: "Тимур Бекмуханов",
    selected_program: "Innovative IT Product Design and Development",
    review_priority_index: 0.72,
    recommendation_status: "RECOMMEND",
    confidence: 0.76,
    shortlist_eligible: true,
    ranking_position: 4,
    top_strengths: ["Хорошее этическое мышление"],
    caution_flags: ["Расхождение эссе и транскрипта"],
    created_at: "2026-03-27T16:20:00Z",
  },
  {
    candidate_id: "a5e6f7a8-b9c0-1234-efab-345678901234",
    name: "Мадина Оспанова",
    selected_program: "Innovative IT Product Design and Development",
    review_priority_index: 0.67,
    recommendation_status: "RECOMMEND",
    confidence: 0.71,
    shortlist_eligible: true,
    ranking_position: 5,
    top_strengths: ["Соответствие программе", "Установка на рост"],
    caution_flags: [],
    created_at: "2026-03-27T14:00:00Z",
  },
  {
    candidate_id: "b6f7a8b9-c0d1-2345-fabc-456789012345",
    name: "Арман Жунусов",
    selected_program: "Innovative IT Product Design and Development",
    review_priority_index: 0.53,
    recommendation_status: "REVIEW_NEEDED",
    confidence: 0.61,
    shortlist_eligible: false,
    ranking_position: 6,
    top_strengths: ["Инициативность"],
    caution_flags: ["Низкая уверенность ASR", "Короткое видео"],
    created_at: "2026-03-27T12:30:00Z",
  },
  {
    candidate_id: "c7a8b9c0-d1e2-3456-abcd-567890123456",
    name: "Камила Ахметова",
    selected_program: "Innovative IT Product Design and Development",
    review_priority_index: 0.48,
    recommendation_status: "REVIEW_NEEDED",
    confidence: 0.55,
    shortlist_eligible: false,
    ranking_position: 7,
    top_strengths: ["Коммуникация"],
    caution_flags: ["Возможно ИИ-написанное эссе"],
    created_at: "2026-03-27T11:00:00Z",
  },
  {
    candidate_id: "d8b9c0d1-e2f3-4567-bcde-678901234567",
    name: "Ерлан Касымов",
    selected_program: "Innovative IT Product Design and Development",
    review_priority_index: 0.38,
    recommendation_status: "LOW_SIGNAL",
    confidence: 0.42,
    shortlist_eligible: false,
    ranking_position: 8,
    top_strengths: [],
    caution_flags: ["Неполная заявка", "Нет видео"],
    created_at: "2026-03-26T17:45:00Z",
  },
];

export function getMockCandidateDetail(id: string): CandidateDetail | null {
  const candidate = MOCK_CANDIDATES.find((c) => c.candidate_id === id);
  if (!candidate) return null;

  return {
    score: {
      candidate_id: candidate.candidate_id,
      selected_program: candidate.selected_program,
      program_id: "prog-it-design-001",
      sub_scores: {
        leadership_potential: 0.78 + Math.random() * 0.15,
        growth_trajectory: 0.72 + Math.random() * 0.2,
        motivation_clarity: 0.68 + Math.random() * 0.2,
        initiative_agency: 0.65 + Math.random() * 0.25,
        learning_agility: 0.7 + Math.random() * 0.2,
        communication_clarity: 0.66 + Math.random() * 0.22,
        ethical_reasoning: 0.6 + Math.random() * 0.3,
        program_fit: 0.62 + Math.random() * 0.28,
      },
      review_priority_index: candidate.review_priority_index,
      recommendation_status: candidate.recommendation_status,
      decision_summary: `Кандидат демонстрирует ${candidate.recommendation_status === "STRONG_RECOMMEND" ? "выдающийся" : "заметный"} потенциал по нескольким направлениям.`,
      confidence: candidate.confidence,
      confidence_band: candidate.confidence > 0.75 ? "HIGH" : "MEDIUM",
      manual_review_required: candidate.caution_flags.length > 0,
      human_in_loop_required: true,
      uncertainty_flag: candidate.confidence < 0.6,
      shortlist_eligible: candidate.shortlist_eligible,
      review_recommendation:
        candidate.recommendation_status === "STRONG_RECOMMEND"
          ? "FAST_TRACK_REVIEW"
          : "STANDARD_REVIEW",
      review_reasons: candidate.caution_flags,
      top_strengths: candidate.top_strengths,
      top_risks: candidate.caution_flags,
      ranking_position: candidate.ranking_position,
      caution_flags: candidate.caution_flags,
      scoring_version: "m6-v1",
    },
    explanation: {
      candidate_id: candidate.candidate_id,
      scoring_version: "m6-v1",
      selected_program: candidate.selected_program,
      recommendation_status: candidate.recommendation_status,
      review_priority_index: candidate.review_priority_index,
      confidence: candidate.confidence,
      manual_review_required: candidate.caution_flags.length > 0,
      human_in_loop_required: true,
      review_recommendation:
        candidate.recommendation_status === "STRONG_RECOMMEND"
          ? "FAST_TRACK_REVIEW"
          : "STANDARD_REVIEW",
      summary: `Кандидат демонстрирует ${candidate.recommendation_status === "STRONG_RECOMMEND" ? "исключительный" : "хороший"} лидерский потенциал и траекторию роста. Видеоинтервью показывает искреннюю вовлечённость в цели программы и чёткое изложение пути личностного развития.`,
      positive_factors: [
        {
          factor: "leadership_potential",
          title: "Сильные индикаторы лидерства",
          summary:
            "Руководил молодёжным волонтёрским проектом с участием 40+ человек в трёх городах",
          score: 0.85,
          score_contribution: 0.17,
          evidence: [
            {
              source: "video_transcript",
              quote:
                "Я организовал волонтёрскую сеть в Алматы, Астане и Шымкенте — всего мы охватили 40 студентов",
            },
            {
              source: "essay",
              quote:
                "Самым сложным было не планирование, а поддержание мотивации команды в трудные моменты",
            },
          ],
        },
        {
          factor: "growth_trajectory",
          title: "Чёткая траектория роста",
          summary:
            "Демонстрирует прогрессию от индивидуального участника до лидера команды за 2 года",
          score: 0.82,
          score_contribution: 0.15,
          evidence: [
            {
              source: "video_transcript",
              quote:
                "Два года назад я едва мог выступать перед группой. Сейчас я веду воркшопы каждый месяц",
            },
          ],
        },
        {
          factor: "motivation_clarity",
          title: "Искренняя мотивация к программе",
          summary:
            "Чётко формулирует конкретные аспекты учебной программы, соответствующие карьерным целям",
          score: 0.78,
          score_contribution: 0.12,
          evidence: [
            {
              source: "essay",
              quote:
                "Модуль продуктового дизайна, сочетающий UX-исследования с валидацией рынка — именно то, что нужно моему стартапу",
            },
          ],
        },
      ],
      caution_blocks:
        candidate.caution_flags.length > 0
          ? [
              {
                flag: candidate.caution_flags[0],
                severity: "advisory",
                title: candidate.caution_flags[0],
                summary:
                  "Автоматический анализ пометил эту область для проверки человеком",
                suggested_action:
                  "Просмотрите выделенные разделы и сравните с видеоинтервью",
              },
            ]
          : [],
      reviewer_guidance:
        "Обратите внимание на подлинность нарратива роста кандидата и верифицируйте заявления по приложенной проектной документации.",
      data_quality_notes: [
        "Уверенность транскрипта видео: 0.91 (высокая)",
        "Внутренний тест: полностью завершён",
        "Эссе: 850 слов, в пределах нормы",
      ],
    },
  };
}

export const MOCK_AUDIT_LOG: ReviewerAction[] = [
  {
    id: "act-001",
    candidate_id: "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
    reviewer_id: "reviewer-1",
    action_type: "shortlist_add",
    previous_status: "STRONG_RECOMMEND",
    new_status: "STRONG_RECOMMEND",
    comment: "Отличный кандидат — добавлен в шорт-лист",
    created_at: "2026-03-28T14:00:00Z",
  },
  {
    id: "act-002",
    candidate_id: "f4d5e6f7-a8b9-0123-defa-234567890123",
    reviewer_id: "reviewer-2",
    action_type: "comment",
    previous_status: "RECOMMEND",
    new_status: "RECOMMEND",
    comment: "Расхождение эссе-транскрипт незначительно — разница в лексике вероятно из-за смены языка",
    created_at: "2026-03-28T15:30:00Z",
  },
  {
    id: "act-003",
    candidate_id: "c7a8b9c0-d1e2-3456-abcd-567890123456",
    reviewer_id: "reviewer-1",
    action_type: "override",
    previous_status: "REVIEW_NEEDED",
    new_status: "RECOMMEND",
    comment: "После ручной проверки флаг ИИ по эссе — ложное срабатывание. Повышаю до RECOMMEND.",
    created_at: "2026-03-28T16:15:00Z",
  },
];
