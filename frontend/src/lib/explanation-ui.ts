import type { CautionBlock, ExplanationReport, FactorBlock } from "@/types";
import { localizeLabel, localizeSeverity } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n";

export function detectContentLocale(text: string): Locale | null {
  const cyrillic = (text.match(/[А-Яа-яЁё]/g) ?? []).length;
  const latin = (text.match(/[A-Za-z]/g) ?? []).length;

  if (cyrillic === 0 && latin === 0) {
    return null;
  }

  return cyrillic >= latin ? "ru" : "en";
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatSources(factor: FactorBlock, locale: Locale): string {
  const sources = Array.from(
    new Set(
      factor.evidence.flatMap((item) =>
        item.source
          .split(",")
          .map((part) => part.trim())
          .filter(Boolean),
      ),
    ),
  );

  if (!sources.length) {
    return locale === "ru" ? "материалы кандидата" : "the candidate materials";
  }

  return sources.map((source) => localizeLabel(source, locale)).join(", ");
}

export function buildLocalizedExplanationSummary(
  explanation: ExplanationReport,
  locale: Locale,
): string {
  const strengths = explanation.positive_factors
    .slice(0, 2)
    .map((factor) =>
      locale === "ru"
        ? `«${localizeLabel(factor.factor, locale)}»`
        : `"${localizeLabel(factor.factor, locale)}"`,
    )
    .join(", ");

  const caution = explanation.caution_blocks[0];

  if (locale === "ru") {
    if (explanation.manual_review_required) {
      return strengths
        ? `Кандидат показывает убедительные сигналы по направлениям ${strengths}, однако кейс требует ручной проверки. Текущей доказательной базы недостаточно для автоматического финального вывода.`
        : "Кандидат требует ручной проверки: текущей доказательной базы недостаточно для автоматического финального вывода.";
    }

    if (caution) {
      return strengths
        ? `Кандидат выглядит уверенно по направлениям ${strengths}, однако перед финальным решением комиссии необходимо отдельно проверить сигнал «${localizeLabel(caution.flag, locale)}».`
        : `Перед финальным решением комиссии необходимо отдельно проверить сигнал «${localizeLabel(caution.flag, locale)}».`;
    }

    return strengths
      ? `Кандидат демонстрирует сильные стороны по направлениям ${strengths}. Текущий профиль выглядит достаточно устойчивым для стандартного рассмотрения комиссией.`
      : "Профиль кандидата выглядит достаточно устойчивым для стандартного рассмотрения комиссией.";
  }

  if (explanation.manual_review_required) {
    return strengths
      ? `The candidate shows strong signals in ${strengths}, but the case should remain in manual review. The current evidence base is not stable enough for a final automated conclusion.`
      : "The candidate should remain in manual review because the current evidence base is not stable enough for a final automated conclusion.";
  }

  if (caution) {
    return strengths
      ? `The candidate looks strong in ${strengths}, but the committee should separately validate the signal "${localizeLabel(caution.flag, locale)}" before the final decision.`
      : `The committee should separately validate the signal "${localizeLabel(caution.flag, locale)}" before the final decision.`;
  }

  return strengths
    ? `The candidate shows strong signals in ${strengths}. The current profile looks stable enough for standard committee review.`
    : "The current candidate profile looks stable enough for standard committee review.";
}

export function buildLocalizedFactorSummary(
  factor: FactorBlock,
  locale: Locale,
): string {
  const title = localizeLabel(factor.factor, locale);
  const score = formatPercent(factor.score);
  const contribution = formatPercent(factor.score_contribution);
  const sources = formatSources(factor, locale);

  if (locale === "ru") {
    return `«${title}» поддерживает итоговую рекомендацию: «СИЛА СИГНАЛА: ${score}», «ВКЛАД: ${contribution}», «ИСТОЧНИКИ: ${sources}».`;
  }

  return `"${title}" supports the final recommendation: "SIGNAL STRENGTH: ${score}", "CONTRIBUTION: ${contribution}", "SOURCES: ${sources}".`;
}

export function buildLocalizedCautionSummary(
  caution: CautionBlock,
  locale: Locale,
): string {
  const severity = localizeSeverity(caution.severity, locale).toLowerCase();
  const title = localizeLabel(caution.flag, locale);

  if (locale === "ru") {
    return `Сигнал «${title}» отмечен как ${severity}. Для комиссии это зона дополнительной проверки: стоит отдельно сверить материалы кандидата и формулировки перед финальным решением.`;
  }

  return `The signal "${title}" is marked as ${severity}. For the committee, this is a review zone: validate the supporting materials and the candidate wording before the final decision.`;
}
