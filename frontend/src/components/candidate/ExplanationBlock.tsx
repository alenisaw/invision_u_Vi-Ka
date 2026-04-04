import { useEffect, useMemo, useState } from "react";
import type { ExplainabilityReport } from "@/types";
import { useLocale } from "@/components/providers/LocaleProvider";
import { localizeLabel, localizeSeverity } from "@/lib/i18n";
import {
  buildLocalizedCautionSummary,
  buildLocalizedExplanationSummary,
  buildLocalizedFactorSummary,
  detectContentLocale,
} from "@/lib/explanation-ui";
import EvidenceList from "./EvidenceList";

interface ExplanationBlockProps {
  explanation: ExplainabilityReport;
  insertAfterConclusion?: React.ReactNode;
}

const RU_INTERFACE = "\u041d\u0430 \u044f\u0437\u044b\u043a\u0435 \u0438\u043d\u0442\u0435\u0440\u0444\u0435\u0439\u0441\u0430";
const RU_ORIGINAL = "\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b";
const RU_AI_TITLE = "\u0412\u044b\u0432\u043e\u0434\u044b \u043e\u0442 \u0418\u0418";
const RU_VERIFY =
  "\u0441\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0430\u044e\u0449\u0438\u0435 \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u044b \u0438 \u0444\u043e\u0440\u043c\u0443\u043b\u0438\u0440\u043e\u0432\u043a\u0438 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0430";

export default function ExplanationBlock({
  explanation,
  insertAfterConclusion,
}: ExplanationBlockProps) {
  const { locale, t } = useLocale();
  const originalLocale = useMemo(
    () => detectContentLocale(explanation.summary),
    [explanation.summary],
  );
  const hasAltView = Boolean(originalLocale && originalLocale !== locale);
  const [viewMode, setViewMode] = useState<"localized" | "original">(
    hasAltView ? "localized" : "original",
  );

  useEffect(() => {
    setViewMode(hasAltView ? "localized" : "original");
  }, [hasAltView, locale]);

  const labels = useMemo(
    () => ({
      title: locale === "ru" ? RU_AI_TITLE : t("explanation.title"),
      strengths: t("explanation.positive"),
      cautions: t("explanation.cautions"),
      localized: locale === "ru" ? RU_INTERFACE : "Interface language",
      original: locale === "ru" ? RU_ORIGINAL : "Original",
    }),
    [locale, t],
  );

  const summaryText =
    viewMode === "localized" && hasAltView
      ? buildLocalizedExplanationSummary(explanation, locale)
      : explanation.summary;

  return (
    <div className="flex flex-col gap-5">
      <div className="card p-6">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="eyebrow">{labels.title}</div>
          {hasAltView ? (
            <div className="flex rounded-full border border-[var(--brand-line)] bg-[var(--surface-subtle)] p-1">
              <button
                type="button"
                onClick={() => setViewMode("localized")}
                className={`rounded-full px-3 py-1.5 text-[0.74rem] font-[800] transition-colors ${
                  viewMode === "localized"
                    ? "bg-[var(--brand-ink)] text-[var(--brand-paper)]"
                    : "text-muted-strong"
                }`}
              >
                {labels.localized}
              </button>
              <button
                type="button"
                onClick={() => setViewMode("original")}
                className={`rounded-full px-3 py-1.5 text-[0.74rem] font-[800] transition-colors ${
                  viewMode === "original"
                    ? "bg-[var(--brand-ink)] text-[var(--brand-paper)]"
                    : "text-muted-strong"
                }`}
              >
                {labels.original}
              </button>
            </div>
          ) : null}
        </div>

        <p className="text-[0.95rem] font-[500] leading-[1.9] text-muted-strong">
          {summaryText}
        </p>
      </div>

      {insertAfterConclusion}

      {explanation.positive_factors.length > 0 ? (
        <div className="card p-6">
          <div className="eyebrow mb-5">{labels.strengths}</div>
          <div className="flex flex-col gap-4">
            {explanation.positive_factors.map((factor) => (
              <div
                key={factor.factor}
                className="rounded-[1rem] border border-[var(--brand-line)] p-5"
                style={{
                  background:
                    "linear-gradient(180deg, color-mix(in srgb, var(--badge-lime-bg) 70%, transparent), var(--surface-subtle))",
                }}
              >
                <div className="mb-3 flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center sm:gap-4">
                  <h4 className="text-[0.95rem] font-[800] leading-tight">
                    {localizeLabel(factor.factor, locale) || factor.title}
                  </h4>
                  <span className="badge badge--lime shrink-0 text-[0.76rem] font-numbers">
                    +{(factor.score_contribution * 100).toFixed(0)}%
                  </span>
                </div>

                <p className="mb-4 text-[0.85rem] leading-relaxed text-muted-strong">
                  {viewMode === "localized" && hasAltView
                    ? buildLocalizedFactorSummary(factor, locale)
                    : factor.summary}
                </p>

                {factor.evidence.length > 0 ? <EvidenceList evidence={factor.evidence} /> : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {explanation.caution_blocks.length > 0 ? (
        <div className="card p-6">
          <div className="eyebrow mb-5">{labels.cautions}</div>
          <div className="flex flex-col gap-4">
            {explanation.caution_blocks.map((caution) => (
              <div
                key={caution.flag}
                className="rounded-[1rem] border border-[var(--brand-line)] p-5"
                style={{
                  background:
                    "linear-gradient(180deg, color-mix(in srgb, var(--badge-coral-bg) 68%, transparent), var(--surface-subtle))",
                }}
              >
                <div className="mb-3 flex items-center gap-3">
                  <span className="badge badge--coral shrink-0 text-[0.72rem] uppercase">
                    {localizeSeverity(caution.severity, locale)}
                  </span>
                  <h4 className="text-[0.95rem] font-[800] leading-tight">
                    {localizeLabel(caution.flag, locale) || caution.title}
                  </h4>
                </div>

                <p className="mb-3 text-[0.85rem] leading-relaxed text-muted-strong">
                  {viewMode === "localized" && hasAltView
                    ? buildLocalizedCautionSummary(caution, locale)
                    : caution.summary}
                </p>

                <p className="mt-2 inline-block rounded-[0.5rem] bg-[var(--brand-coral)]/10 px-3 py-1.5 text-[0.82rem] font-[700] text-[var(--brand-coral)]">
                  {viewMode === "localized" && hasAltView
                    ? t("explanation.check", {
                        action: locale === "ru" ? RU_VERIFY : "review the supporting materials and the candidate wording",
                      })
                    : t("explanation.check", { action: caution.suggested_action })}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
