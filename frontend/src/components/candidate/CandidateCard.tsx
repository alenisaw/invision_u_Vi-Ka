import type { CandidateScore } from "@/types";
import { formatPercent, SUB_SCORE_LABELS } from "@/lib/utils";
import StatusBadge from "@/components/dashboard/StatusBadge";

interface CandidateCardProps {
  score: CandidateScore;
}

export default function CandidateCard({ score }: CandidateCardProps) {
  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="eyebrow mb-2">Обзор кандидата</div>
          <h2 className="text-[1.22rem] font-[800] leading-[1.1]">
            {score.selected_program}
          </h2>
        </div>
        <StatusBadge status={score.recommendation_status} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Балл RPI" value={formatPercent(score.review_priority_index)} accent />
        <MetricCard label="Уверенность" value={formatPercent(score.confidence)} />
        <MetricCard label="Диапазон" value={score.confidence_band} />
        <MetricCard label="Ранг" value={score.ranking_position ? `#${score.ranking_position}` : "—"} />
      </div>

      <div className="eyebrow mb-3">Под-оценки</div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {Object.entries(score.sub_scores).map(([key, value]) => (
          <div
            key={key}
            className="flex items-center justify-between px-3 py-2.5 rounded-[1rem]"
            style={{ background: "var(--surface-subtle)" }}
          >
            <span className="text-[0.78rem] font-[600] text-muted-strong">
              {SUB_SCORE_LABELS[key] ?? key}
            </span>
            <span className="text-[0.88rem] font-[800]">{formatPercent(value)}</span>
          </div>
        ))}
      </div>

      {score.top_strengths.length > 0 && (
        <div className="mt-5">
          <div className="eyebrow mb-2">Сильные стороны</div>
          <div className="flex flex-wrap gap-2">
            {score.top_strengths.map((s) => (
              <span key={s} className="badge badge--blue">{s}</span>
            ))}
          </div>
        </div>
      )}

      {score.caution_flags.length > 0 && (
        <div className="mt-4">
          <div className="eyebrow mb-2">Предупреждения</div>
          <div className="flex flex-wrap gap-2">
            {score.caution_flags.map((f) => (
              <span key={f} className="badge badge--coral">{f}</span>
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
        className={`text-[0.72rem] font-[700] uppercase tracking-[0.1em] mb-1 ${accent ? 'opacity-70 text-black' : 'text-muted'}`}
      >
        {label}
      </div>
      <div className={`text-[1.16rem] font-[800] ${accent ? 'text-black' : ''}`}>
        {value}
      </div>
    </div>
  );
}