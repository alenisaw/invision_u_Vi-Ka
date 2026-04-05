import type { CandidateScore } from "@/types";
import { useLocale } from "@/components/providers/LocaleProvider";
import {
  formatPercent,
  getAiRiskLevel,
  localizeLabel,
  localizeLabels,
  localizeProgramName,
} from "@/lib/i18n";
import StatusBadge from "@/components/dashboard/StatusBadge";

interface CandidateCardProps {
  score: CandidateScore;
}

export default function CandidateCard({ score }: CandidateCardProps) {
  const { locale, t } = useLocale();
  const aiRisk = getAiRiskLevel(score.caution_flags);
  const aiRiskTone =
    aiRisk === "high" ? "badge--coral" : aiRisk === "review" ? "badge--neutral" : "badge--blue";
  const aiRiskLabel = t(`dashboard.aiRisk.${aiRisk}`);
  const aiRiskDescription =
    aiRisk === "high"
      ? locale === "ru"
        ? "Обнаружены сигналы, требующие отдельной проверки на недостоверность, синтетическую речь или AI-assisted writing."
        : "Signals suggest a heightened need to verify authenticity, synthetic speech, or AI-assisted writing."
      : aiRisk === "review"
        ? locale === "ru"
          ? "Есть косвенные расхождения по стилю, аудио или источникам. Желательна дополнительная проверка."
          : "There are indirect style, audio, or source inconsistencies. A manual review is recommended."
        : locale === "ru"
          ? "Сильных сигналов AI-помощи, синтетической речи или недостоверности не выявлено."
          : "No strong signs of AI-assisted writing, synthetic speech, or authenticity issues were detected.";

  return (
    <div className="card p-6">
      <div className="mb-5 flex items-start justify-between">
        <div>
          <div className="eyebrow mb-2">{t("dashboard.overview")}</div>
          <h2 className="text-[1.22rem] font-[800] leading-[1.1]">
            {localizeProgramName(score.selected_program, locale)}
          </h2>
        </div>
        <StatusBadge status={score.recommendation_status} />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <MetricCard
          label={t("dashboard.rpiScore")}
          value={formatPercent(score.review_priority_index)}
          accent
        />
        <MetricCard label={t("common.confidence")} value={formatPercent(score.confidence)} />
        <MetricCard
          label={t("dashboard.rank")}
          value={score.ranking_position ? `#${score.ranking_position}` : t("common.none")}
        />
      </div>

      <div className="mb-6 rounded-[1.1rem] border border-[var(--brand-line)] bg-[linear-gradient(180deg,var(--surface-soft),var(--surface-subtle))] px-4 py-4">
        <div className="mb-2 flex items-center justify-between gap-3">
          <div className="text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
            {locale === "ru" ? "Проверка аутентичности" : "Authenticity advisory"}
          </div>
          <span className={`badge ${aiRiskTone}`}>{aiRiskLabel}</span>
        </div>
        <div className="text-[0.85rem] leading-[1.7] text-muted-strong">{aiRiskDescription}</div>
      </div>

      <div className="eyebrow mb-3">{t("dashboard.subscores")}</div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Object.entries(score.sub_scores).map(([key, value]) => (
          <div
            key={key}
            className="flex items-center justify-between gap-3 rounded-[1rem] px-3 py-2.5"
            style={{ background: "var(--surface-subtle)" }}
          >
            <span className="truncate text-[0.78rem] font-[600] text-muted-strong">
              {localizeLabel(key, locale)}
            </span>
            <span className="text-right text-[0.88rem] font-[800]">{formatPercent(value)}</span>
          </div>
        ))}
      </div>

      {score.top_strengths.length > 0 ? (
        <div className="mt-5">
          <div className="eyebrow mb-2">{t("dashboard.strengths")}</div>
          <div className="flex flex-wrap gap-2">
            {localizeLabels(score.top_strengths, locale).map((strength) => (
              <span key={strength} className="badge badge--blue">
                {strength}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {score.caution_flags.length > 0 ? (
        <div className="mt-4">
          <div className="eyebrow mb-2">{t("dashboard.cautions")}</div>
          <div className="flex flex-wrap gap-2">
            {localizeLabels(score.caution_flags, locale).map((flag) => (
              <span key={flag} className="badge badge--coral">
                {flag}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MetricCard({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div
      className="rounded-[var(--radius-md)] px-4 py-3"
      style={{
        background: accent ? "var(--brand-lime)" : "var(--surface-subtle)",
      }}
    >
      <div
        className={`mb-1 text-[0.72rem] font-[700] uppercase tracking-[0.1em] ${
          accent ? "text-black opacity-70" : "text-muted"
        }`}
      >
        {label}
      </div>
      <div className={`text-[1.16rem] font-[800] ${accent ? "text-black" : ""}`}>{value}</div>
    </div>
  );
}
