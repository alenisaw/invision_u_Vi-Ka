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

// Используем системные цвета вместо жестко заданных HEX
const COLORS = [
  "var(--brand-lime)",
  "var(--brand-blue)",
  "var(--brand-coral)"
];

interface CandidateData {
  name: string;
  subScores: SubScores;
}

interface CompareRadarProps {
  candidates: CandidateData[];
}

export default function CompareRadar({ candidates }: CompareRadarProps) {
  if (candidates.length === 0) return null;

  const dimensions = Object.keys(candidates[0].subScores);

  const data = dimensions.map((key) => {
    const row: Record<string, string | number> = {
      dimension: SUB_SCORE_LABELS[key] ?? key,
    };
    candidates.forEach((c, i) => {
      row[`candidate_${i}`] = Math.round((c.subScores[key] ?? 0) * 100);
    });
    return row;
  });

  return (
    <div className="card p-6">
      <div className="eyebrow mb-4">Сравнение профилей</div>
      <ResponsiveContainer width="100%" height={380}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="68%">
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
          {candidates.map((c, i) => (
            <Radar
              key={c.name}
              name={c.name}
              dataKey={`candidate_${i}`}
              // Берем цвета по кругу, если кандидатов больше 3
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length]}
              fillOpacity={0.15}
              strokeWidth={2}
            />
          ))}
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
          <Legend
            wrapperStyle={{ 
              fontSize: "0.82rem", 
              fontWeight: 700, 
              color: "var(--brand-muted-strong)" 
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}