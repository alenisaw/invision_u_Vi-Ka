import type { ExplainabilityReport } from "@/types";
import { useLocale } from "@/components/providers/LocaleProvider";
import { localizeLabel, localizeSeverity } from "@/lib/i18n";
import EvidenceList from "./EvidenceList";

interface ExplanationBlockProps {
  explanation: ExplainabilityReport;
  insertAfterConclusion?: React.ReactNode;
}

export default function ExplanationBlock({
  explanation,
  insertAfterConclusion,
}: ExplanationBlockProps) {
  const { locale, t } = useLocale();

  return (
    <div className="flex flex-col gap-5">
      <div className="card p-6">
        <div className="eyebrow mb-3">{t("explanation.title")}</div>
        <p className="text-[0.95rem] font-[500] leading-relaxed text-muted-strong">
          {explanation.summary}
        </p>
      </div>

      {insertAfterConclusion}

      {explanation.positive_factors.length > 0 && (
        <div className="card p-6">
          <div className="eyebrow mb-5">{t("explanation.positive")}</div>
          <div className="flex flex-col gap-4">
            {explanation.positive_factors.map((factor) => (
              <div
                key={factor.factor}
                className="rounded-[1rem] p-5 bg-[var(--brand-lime)]/10"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-4 mb-3">
                  <h4 className="text-[0.95rem] font-[800] leading-tight">
                    {localizeLabel(factor.factor, locale) || factor.title}
                  </h4>
                  <span className="badge badge--lime text-[0.76rem] font-numbers shrink-0">
                    +{(factor.score_contribution * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-[0.85rem] mb-4 text-muted-strong leading-relaxed">
                  {factor.summary}
                </p>
                {factor.evidence.length > 0 && <EvidenceList evidence={factor.evidence} />}
              </div>
            ))}
          </div>
        </div>
      )}

      {explanation.caution_blocks.length > 0 && (
        <div className="card p-6">
          <div className="eyebrow mb-5">{t("explanation.cautions")}</div>
          <div className="flex flex-col gap-4">
            {explanation.caution_blocks.map((caution) => (
              <div
                key={caution.flag}
                className="rounded-[1rem] p-5 bg-[var(--brand-coral)]/10"
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="badge badge--coral text-[0.72rem] shrink-0 uppercase">
                    {localizeSeverity(caution.severity, locale)}
                  </span>
                  <h4 className="text-[0.95rem] font-[800] leading-tight">
                    {localizeLabel(caution.flag, locale) || caution.title}
                  </h4>
                </div>
                <p className="text-[0.85rem] mb-3 text-muted-strong leading-relaxed">
                  {caution.summary}
                </p>
                <p className="text-[0.82rem] font-[700] text-[var(--brand-coral)] mt-2 bg-[var(--brand-coral)]/10 inline-block px-3 py-1.5 rounded-[0.5rem]">
                  {t("explanation.check", { action: caution.suggested_action })}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
