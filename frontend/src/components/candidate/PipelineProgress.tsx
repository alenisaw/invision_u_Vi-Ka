"use client";

import { useLocale } from "@/components/providers/LocaleProvider";

const STEP_IDS = ["m2", "asr", "m3", "m4", "m5", "m6", "m7"] as const;

interface PipelineProgressProps {
  status: "idle" | "running" | "completed" | "error";
  currentStep: number;
}

export default function PipelineProgress({ status, currentStep }: PipelineProgressProps) {
  const { t } = useLocale();

  return (
    <div className="flex flex-wrap gap-2 items-center">
      {STEP_IDS.map((stepId, index) => {
        const isCompleted = status === "completed" || (status === "running" && index < currentStep);
        const isCurrent = status === "running" && index === currentStep;
        const isError = status === "error" && index === currentStep;

        return (
          <span key={stepId} className="flex items-center gap-2">
            <span
              className="px-3 py-1.5 rounded-full text-[0.78rem] font-[700] transition-all duration-300"
              style={{
                background: isError
                  ? "rgba(255, 100, 80, 0.85)"
                  : isCompleted
                    ? "var(--brand-lime)"
                    : isCurrent
                      ? "var(--brand-blue)"
                      : "rgba(255, 255, 255, 0.12)",
                color: isError
                  ? "#ffffff"
                  : isCompleted || isCurrent
                    ? "#1a1a1a"
                    : "rgba(255, 255, 255, 0.5)",
                ...(isCurrent ? { animation: "pulse-step 1.2s ease-in-out infinite" } : {}),
              }}
            >
              {t(`pipeline.step.${stepId}`)}
            </span>
            {index < STEP_IDS.length - 1 && (
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
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </div>
  );
}
