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
          <PolarGrid stroke="rgba(20, 20, 20, 0.08)" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fontSize: 11, fontWeight: 700, fill: "rgba(20, 20, 20, 0.62)" }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: "rgba(20, 20, 20, 0.4)" }}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#c1f11d"
            fill="rgba(193, 241, 29, 0.35)"
            fillOpacity={0.6}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              background: "#141414",
              color: "#ffffff",
              border: "none",
              borderRadius: "0.9rem",
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
