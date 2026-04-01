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
import type { SubScores } from "@/types";
import { SUB_SCORE_LABELS } from "@/lib/utils";

interface ScoreRadarProps {
  subScores: SubScores;
}

export default function ScoreRadar({ subScores }: ScoreRadarProps) {
  const data = Object.entries(subScores).map(([key, value]) => ({
    dimension: SUB_SCORE_LABELS[key] ?? key,
    score: Math.round(value * 100),
    fullMark: 100,
  }));

  return (
    <div className="card p-6">
      <div className="eyebrow mb-4">Профиль оценок</div>
      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
          <PolarGrid stroke="var(--brand-line)" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fontSize: 11, fontWeight: 700, fill: "var(--brand-muted-strong)" }}
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
              background: "var(--brand-ink)",
              color: "var(--brand-paper)",
              border: "none",
              borderRadius: "1rem",
              fontSize: "0.82rem",
              fontWeight: 700,
            }}
            formatter={(value: number) => [`${value}%`, "Балл"]}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}