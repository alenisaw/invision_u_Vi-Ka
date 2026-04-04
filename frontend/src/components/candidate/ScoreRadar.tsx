"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { useLocale } from "@/components/providers/LocaleProvider";
import type { SubScores } from "@/types";
import { localizeLabel } from "@/lib/i18n";

interface ScoreRadarProps {
  subScores: SubScores;
}

interface CustomTickProps {
  payload?: {
    value: string;
  };
  x?: number;
  y?: number;
  cx?: number;
  cy?: number;
}

function CustomAngleTick(props: CustomTickProps) {
  const { payload, x = 0, y = 0, cx = 0, cy = 0 } = props;

  const dx = x - cx;
  const dy = y - cy;
  const distance = Math.sqrt(dx * dx + dy * dy) || 1;

  const offset = 20;

  const newX = x + (dx / distance) * offset;
  const newY = y + (dy / distance) * offset;

  let textAnchor: "start" | "middle" | "end" = "middle";

  if (dx > 12) {
    textAnchor = "start";
  } else if (dx < -12) {
    textAnchor = "end";
  }

  return (
    <text
      x={newX}
      y={newY}
      textAnchor={textAnchor}
      dominantBaseline="middle"
      fontSize={11}
      fontWeight={700}
      fill="var(--brand-muted-strong)"
    >
      {payload?.value}
    </text>
  );
}

export default function ScoreRadar({ subScores }: ScoreRadarProps) {
  const { locale, t } = useLocale();

  const data = Object.entries(subScores).map(([key, value]) => ({
    dimension: localizeLabel(key, locale),
    score: Math.round(value * 100),
    fullMark: 100,
  }));

  return (
    <div className="card p-6">
      <div className="eyebrow mb-4">{t("radar.scoreProfile")}</div>

      <ResponsiveContainer width="100%" height={360}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="58%">
          <PolarGrid stroke="var(--brand-line)" />

          <PolarAngleAxis
            dataKey="dimension"
            tick={<CustomAngleTick />}
          />

          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: "var(--brand-muted)" }}
          />

          <Radar
            name="Score"
            dataKey="score"
            stroke="var(--brand-lime)"
            fill="var(--brand-lime)"
            fillOpacity={0.35}
            strokeWidth={2}
          />

          <Tooltip
            contentStyle={{
              background: "var(--brand-paper)",
              color: "var(--brand-ink)",
              border: "none",
              borderRadius: "1rem",
              fontSize: "0.82rem",
              fontWeight: 700,
            }}
            formatter={(value: number) => [`${value}%`, t("radar.tooltipScore")]}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}