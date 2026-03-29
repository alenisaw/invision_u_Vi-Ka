import type { ExplainabilityReport } from "@/types";
import EvidenceList from "./EvidenceList";

interface ExplanationBlockProps {
  explanation: ExplainabilityReport;
}

export default function ExplanationBlock({ explanation }: ExplanationBlockProps) {
  return (
    <div className="flex flex-col gap-5">
      <div className="card p-6">
        <div className="eyebrow mb-3">Заключение ИИ</div>
        <p className="text-[0.95rem] font-[500] leading-[1.5]" style={{ color: "var(--brand-muted-strong)" }}>
          {explanation.summary}
        </p>
      </div>

      {explanation.positive_factors.length > 0 && (
        <div className="card p-6">
          <div className="eyebrow mb-4">Положительные факторы</div>
          <div className="flex flex-col gap-4">
            {explanation.positive_factors.map((factor) => (
              <div
                key={factor.factor}
                className="rounded-[var(--radius-md)] p-4"
                style={{ background: "rgba(193, 241, 29, 0.08)" }}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-[0.92rem] font-[800]">{factor.title}</h4>
                  <span className="badge badge--lime text-[0.72rem]">
                    +{(factor.score_contribution * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-[0.82rem] mb-3" style={{ color: "var(--brand-muted-strong)" }}>
                  {factor.summary}
                </p>
                {factor.evidence.length > 0 && (
                  <EvidenceList evidence={factor.evidence} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {explanation.caution_blocks.length > 0 && (
        <div className="card p-6">
          <div className="eyebrow mb-4">Предупреждения</div>
          <div className="flex flex-col gap-3">
            {explanation.caution_blocks.map((caution) => (
              <div
                key={caution.flag}
                className="rounded-[var(--radius-md)] p-4"
                style={{ background: "rgba(255, 142, 112, 0.08)" }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="badge badge--coral text-[0.72rem]">{caution.severity}</span>
                  <h4 className="text-[0.92rem] font-[800]">{caution.title}</h4>
                </div>
                <p className="text-[0.82rem] mb-2" style={{ color: "var(--brand-muted-strong)" }}>
                  {caution.summary}
                </p>
                <p className="text-[0.78rem] font-[700]" style={{ color: "var(--brand-coral)" }}>
                  Действие: {caution.suggested_action}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card p-6">
        <div className="eyebrow mb-3">Рекомендации рецензенту</div>
        <p className="text-[0.88rem] font-[600]" style={{ color: "var(--brand-muted-strong)" }}>
          {explanation.reviewer_guidance}
        </p>
      </div>

      {explanation.data_quality_notes.length > 0 && (
        <div className="card p-6">
          <div className="eyebrow mb-3">Качество данных</div>
          <ul className="flex flex-col gap-2">
            {explanation.data_quality_notes.map((note) => (
              <li key={note} className="flex items-center gap-2 text-[0.82rem]" style={{ color: "var(--brand-muted-strong)" }}>
                <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: "var(--brand-blue)" }} />
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
