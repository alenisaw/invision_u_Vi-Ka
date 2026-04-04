"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
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

  const offset = 36;
  const newX = x + (dx / distance) * offset;
  const newY = y + (dy / distance) * offset;

  let textAnchor: "start" | "middle" | "end" = "middle";

  if (dx > 12) {
    textAnchor = "start";
  } else if (dx < -12) {
    textAnchor = "end";
  }

  const words = String(payload?.value ?? "").split(" ");
  const midpoint = Math.ceil(words.length / 2);
  const lines =
    words.length > 1
      ? [words.slice(0, midpoint).join(" "), words.slice(midpoint).join(" ")]
      : words;

  return (
    <text
      x={newX}
      y={newY}
      textAnchor={textAnchor}
      dominantBaseline="middle"
      fontSize={11.5}
      fontWeight={700}
      fill="var(--brand-muted-strong)"
    >
      {lines.map((line, index) => (
        <tspan key={`${line}-${index}`} x={newX} dy={index === 0 ? 0 : 13}>
          {line}
        </tspan>
      ))}
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
    <div
      className="card p-6"
      style={{
        background:
          "radial-gradient(circle at 50% 34%, color-mix(in srgb, var(--badge-lime-bg) 20%, transparent), transparent 42%), var(--surface-card)",
      }}
    >
      <div className="eyebrow mb-4">{t("radar.scoreProfile")}</div>

      <ResponsiveContainer width="100%" height={450}>
        <RadarChart data={data} cx="50%" cy="52%" outerRadius="62%">
          <defs>
            <linearGradient id="scoreRadarFill" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="var(--brand-lime)" stopOpacity={0.62} />
              <stop offset="100%" stopColor="var(--brand-blue)" stopOpacity={0.18} />
            </linearGradient>
          </defs>

          <PolarGrid stroke="var(--brand-line)" />
          <PolarAngleAxis dataKey="dimension" tick={<CustomAngleTick />} />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: "var(--brand-muted)" }}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="var(--brand-lime)"
            fill="url(#scoreRadarFill)"
            fillOpacity={1}
            strokeWidth={2.6}
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
