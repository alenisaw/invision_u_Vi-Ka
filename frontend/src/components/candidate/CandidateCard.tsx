import type { CandidateScore } from "@/types";
import { useLocale } from "@/components/providers/LocaleProvider";
import { formatPercent, localizeLabel, localizeLabels } from "@/lib/i18n";
import StatusBadge from "@/components/dashboard/StatusBadge";

interface CandidateCardProps {
  score: CandidateScore;
}

export default function CandidateCard({ score }: CandidateCardProps) {
  const { locale, t } = useLocale();

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="eyebrow mb-2">{t("dashboard.overview")}</div>
          <h2 className="text-[1.22rem] font-[800] leading-[1.1]">
            {score.selected_program}
          </h2>
        </div>
        <StatusBadge status={score.recommendation_status} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <MetricCard label={t("dashboard.rpiScore")} value={formatPercent(score.review_priority_index)} accent />
        <MetricCard label={t("common.confidence")} value={formatPercent(score.confidence)} />
        <MetricCard label={t("dashboard.confidenceBand")} value={score.confidence_band} />
        <MetricCard label={t("dashboard.rank")} value={score.ranking_position ? `#${score.ranking_position}` : t("common.none")} />
      </div>

      <div className="eyebrow mb-3">{t("dashboard.subscores")}</div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Object.entries(score.sub_scores).map(([key, value]) => (
          <div
            key={key}
            className="flex items-center justify-between px-3 py-2.5 rounded-[1rem] gap-3"
            style={{ background: "var(--surface-subtle)" }}
          >
            <span className="text-[0.78rem] font-[600] text-muted-strong truncate">
              {localizeLabel(key, locale)}
            </span>
            <span className="text-[0.88rem] font-[800] text-right">
              {formatPercent(value)}
            </span>
          </div>
        ))}
      </div>

      {score.top_strengths.length > 0 && (
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
      )}

      {score.caution_flags.length > 0 && (
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
      )}
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
        className={`text-[0.72rem] font-[700] uppercase tracking-[0.1em] mb-1 ${
          accent ? "opacity-70 text-black" : "text-muted"
        }`}
      >
        {label}
      </div>
      <div className={`text-[1.16rem] font-[800] ${accent ? "text-black" : ""}`}>
        {value}
      </div>
    </div>
  );
}
