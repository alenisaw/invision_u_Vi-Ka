"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import type { SubScores } from "@/types";
import { SUB_SCORE_LABELS } from "@/lib/utils";

const COLORS = ["#c1f11d", "#3dedf1", "#ff8e70"];

interface CandidateData {
  name: string;
  subScores: SubScores;
}

interface CompareRadarProps {
  candidates: CandidateData[];
}

export default function CompareRadar({ candidates }: CompareRadarProps) {
  if (candidates.length === 0) return null;

  const canonicalKeys = Object.keys(SUB_SCORE_LABELS);

  const data = canonicalKeys.map((key) => {
    const row: Record<string, string | number> = {
      dimension: SUB_SCORE_LABELS[key],
    };
    candidates.forEach((c, i) => {
      row[`candidate_${i}`] = c.subScores[key] != null
        ? Math.round((c.subScores[key] as number) * 100)
        : 0;
    });
    return row;
  });

  return (
    <div className="card p-6">
      <div className="eyebrow mb-4">Сравнение профилей</div>
      <ResponsiveContainer width="100%" height={380}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="68%">
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
          {candidates.map((c, i) => (
            <Radar
              key={c.name}
              name={c.name}
              dataKey={`candidate_${i}`}
              stroke={COLORS[i]}
              fill={COLORS[i]}
              fillOpacity={0.15}
              strokeWidth={2}
            />
          ))}
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
          <Legend
            wrapperStyle={{ fontSize: "0.82rem", fontWeight: 700 }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
