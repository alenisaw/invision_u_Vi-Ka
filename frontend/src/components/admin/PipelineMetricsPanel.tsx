"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { BarChart3, Printer } from "lucide-react";
import type { Locale } from "@/lib/i18n";
import type { PipelineMetrics } from "@/types";
import {
  getPipelineStatusBadge,
  getPipelineStatusLabel,
  localizePipelineFlag,
  localizeStageName,
} from "@/lib/pipeline-ui";

const STAGE_ORDER = ["gateway", "asr", "privacy", "profile", "extraction", "scoring", "explanation"];

export default function PipelineMetricsPanel({
  metrics,
  locale,
  mode = "full",
  showReportLink = false,
}: {
  metrics: PipelineMetrics | null;
  locale: Locale;
  mode?: "compact" | "full";
  showReportLink?: boolean;
}) {
  const labels = {
    title: locale === "ru" ? "Наблюдаемость пайплайна" : "Pipeline observability",
    stageTitle: locale === "ru" ? "Средняя задержка по стадиям" : "Average stage latency",
    fallbackTitle: locale === "ru" ? "Fallback и деградации" : "Fallback and degraded paths",
    qualityTitle: locale === "ru" ? "Частые quality flags" : "Top quality flags",
    recentRuns: locale === "ru" ? "Последние прогоны" : "Recent runs",
    status: locale === "ru" ? "Состояние" : "Status",
    latency: locale === "ru" ? "Задержка" : "Latency",
    totalRuns: locale === "ru" ? "обработок" : "runs",
    degradedRate: locale === "ru" ? "degraded rate" : "degraded rate",
    reviewRate: locale === "ru" ? "manual review" : "manual review",
    avgLatency: locale === "ru" ? "средняя задержка" : "avg latency",
    p95Latency: locale === "ru" ? "p95 задержка" : "p95 latency",
    noMetrics: locale === "ru" ? "Метрики пока не собраны" : "Metrics are not available yet",
    reportLink: locale === "ru" ? "Открыть export/report screen" : "Open export/report screen",
    print: locale === "ru" ? "Печать" : "Print",
  };

  if (!metrics) {
    return (
      <div className="rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-4 py-4 text-[0.9rem] text-muted">
        {labels.noMetrics}
      </div>
    );
  }

  const stageEntries = STAGE_ORDER
    .map((stage) => [stage, metrics.overview.avg_stage_latencies_ms[stage] ?? 0] as const)
    .filter(([, latency]) => latency > 0);

  const fallbackEntries = Object.entries(metrics.overview.fallback_counts)
    .sort((left, right) => right[1] - left[1])
    .slice(0, mode === "full" ? 8 : 4);

  const qualityEntries = Object.entries(metrics.overview.quality_flag_counts)
    .sort((left, right) => right[1] - left[1])
    .slice(0, mode === "full" ? 8 : 4);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="text-[1rem] font-[800]">{labels.title}</div>
        <div className="flex flex-wrap gap-2">
          {showReportLink ? (
            <Link href="/admin/metrics" className="btn btn--ghost btn--sm">
              <BarChart3 className="h-4 w-4" />
              <span>{labels.reportLink}</span>
            </Link>
          ) : null}
          {mode === "full" ? (
            <button
              type="button"
              onClick={() => window.print()}
              className="btn btn--ghost btn--sm"
            >
              <Printer className="h-4 w-4" />
              <span>{labels.print}</span>
            </button>
          ) : null}
        </div>
      </div>

      <div className={`grid gap-4 ${mode === "full" ? "grid-cols-2 xl:grid-cols-5" : "grid-cols-2 xl:grid-cols-5"}`}>
        <StatChip label={labels.totalRuns} value={String(metrics.overview.total_runs)} />
        <StatChip label={labels.degradedRate} value={`${Math.round(metrics.overview.degraded_rate * 100)}%`} />
        <StatChip label={labels.reviewRate} value={`${Math.round(metrics.overview.manual_review_rate * 100)}%`} />
        <StatChip label={labels.avgLatency} value={`${Math.round(metrics.overview.avg_total_latency_ms)}ms`} />
        <StatChip label={labels.p95Latency} value={`${Math.round(metrics.overview.p95_total_latency_ms)}ms`} />
      </div>

      <div className={`grid gap-5 ${mode === "full" ? "xl:grid-cols-[1.4fr_1fr_1fr]" : "xl:grid-cols-[1.2fr_1fr_1fr]"}`}>
        <SectionCard title={labels.stageTitle}>
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
            {stageEntries.map(([stage, latency]) => (
              <MetricTile
                key={stage}
                label={localizeStageName(stage, locale)}
                value={`${Math.round(latency)}ms`}
              />
            ))}
          </div>
        </SectionCard>

        <SectionCard title={labels.fallbackTitle}>
          <div className="flex flex-wrap gap-2">
            {fallbackEntries.length > 0 ? fallbackEntries.map(([flag, count]) => (
              <span key={flag} className="badge badge--coral">
                {localizePipelineFlag(flag, locale)} · {count}
              </span>
            )) : <span className="text-[0.82rem] text-muted">{labels.noMetrics}</span>}
          </div>
        </SectionCard>

        <SectionCard title={labels.qualityTitle}>
          <div className="flex flex-wrap gap-2">
            {qualityEntries.length > 0 ? qualityEntries.map(([flag, count]) => (
              <span key={flag} className="badge badge--neutral">
                {localizePipelineFlag(flag, locale)} · {count}
              </span>
            )) : <span className="text-[0.82rem] text-muted">{labels.noMetrics}</span>}
          </div>
        </SectionCard>
      </div>

      <SectionCard title={labels.recentRuns}>
        <div className={`grid gap-3 ${mode === "full" ? "xl:grid-cols-2" : "xl:grid-cols-2"}`}>
          {metrics.recent_runs.slice(0, mode === "full" ? 8 : 4).map((run) => (
            <div
              key={run.audit_id}
              className="rounded-[1rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-4 py-4"
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-[0.82rem] font-[800] text-[var(--brand-ink)]">
                    {run.candidate_id ? `#${run.candidate_id.slice(0, 8)}` : "System"}
                  </div>
                </div>
                <span className={`badge ${getPipelineStatusBadge(run.pipeline_quality_status)}`}>
                  {getPipelineStatusLabel(run.pipeline_quality_status, locale)}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-[0.8rem]">
                <MetricLine label={labels.latency} value={`${Math.round(run.total_latency_ms)}ms`} />
                <MetricLine label={labels.status} value={getPipelineStatusLabel(run.pipeline_quality_status, locale)} />
              </div>

              {Object.keys(run.stage_latencies_ms).length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {STAGE_ORDER.filter((stage) => run.stage_latencies_ms[stage] != null).map((stage) => (
                    <span key={stage} className="badge badge--blue">
                      {localizeStageName(stage, locale)} · {Math.round(run.stage_latencies_ms[stage])}ms
                    </span>
                  ))}
                </div>
              ) : null}

              {run.quality_flags.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {run.quality_flags.slice(0, 4).map((flag) => (
                    <span key={flag} className="badge badge--coral">
                      {localizePipelineFlag(flag, locale)}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-[1.2rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] p-5">
      <div className="mb-3 text-[0.78rem] font-[800] uppercase tracking-[0.12em] text-muted">
        {title}
      </div>
      {children}
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[0.95rem] bg-[var(--surface-subtle-2)] px-4 py-4">
      <div className="mb-1 text-[0.72rem] font-[800] uppercase tracking-[0.1em] text-muted">
        {label}
      </div>
      <div className="text-[1.1rem] font-[800] font-numbers">{value}</div>
    </div>
  );
}

function MetricLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[0.95rem] bg-[var(--surface-subtle-2)] px-4 py-3">
      <div className="mb-1 text-[0.7rem] font-[800] uppercase tracking-[0.1em] text-muted">
        {label}
      </div>
      <div className="text-[0.9rem] font-[800]">{value}</div>
    </div>
  );
}

function StatChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.1rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] px-5 py-5">
      <div className="mb-2 text-[0.72rem] font-[800] uppercase tracking-[0.12em] text-muted">
        {label}
      </div>
      <div className="text-[1.5rem] font-[900]">{value}</div>
    </div>
  );
}
