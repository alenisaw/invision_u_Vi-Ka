"use client";

const STEPS = [
  { id: "m2", label: "M2 Intake" },
  { id: "m13", label: "M13 ASR" },
  { id: "m3", label: "M3 Privacy" },
  { id: "m4", label: "M4 Profile" },
  { id: "m5", label: "M5 NLP" },
  { id: "m6", label: "M6 Scoring" },
  { id: "m7", label: "M7 Explain" },
] as const;

interface PipelineProgressProps {
  status: "idle" | "running" | "completed" | "error";
  currentStep: number;
}

export default function PipelineProgress({ status, currentStep }: PipelineProgressProps) {
  return (
    <div className="flex flex-wrap gap-2 items-center">
      {STEPS.map((step, i) => {
        const isCompleted = status === "completed" || (status === "running" && i < currentStep);
        const isCurrent = status === "running" && i === currentStep;
        const isError = status === "error" && i === currentStep;

        return (
          <span key={step.id} className="flex items-center gap-2">
            <span
              className="px-3 py-1.5 rounded-full text-[0.78rem] font-[700] transition-all duration-300"
              style={{
                background: isError
                  ? "rgba(255, 142, 112, 0.22)"
                  : isCompleted
                    ? "rgba(193, 241, 29, 0.22)"
                    : isCurrent
                      ? "rgba(61, 237, 241, 0.22)"
                      : "rgba(20, 20, 20, 0.06)",
                color: isError
                  ? "#ac472e"
                  : isCompleted
                    ? "#415005"
                    : isCurrent
                      ? "#0a6a6d"
                      : "var(--brand-muted)",
                ...(isCurrent
                  ? { animation: "pulse-step 1.2s ease-in-out infinite" }
                  : {}),
              }}
            >
              {step.label}
            </span>
            {i < STEPS.length - 1 && (
              <span
                style={{
                  color: isCompleted ? "rgba(193, 241, 29, 0.6)" : "rgba(20, 20, 20, 0.15)",
                }}
              >
                &rarr;
              </span>
            )}
          </span>
        );
      })}

      <style jsx>{`
        @keyframes pulse-step {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
