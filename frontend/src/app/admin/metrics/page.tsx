"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import PipelineMetricsPanel from "@/components/admin/PipelineMetricsPanel";
import { useAuth } from "@/components/providers/AuthProvider";
import { useLocale } from "@/components/providers/LocaleProvider";
import { adminApi } from "@/lib/api";
import type { PipelineMetrics } from "@/types";

export default function AdminMetricsPage() {
  const router = useRouter();
  const { locale } = useLocale();
  const { user, loading: authLoading } = useAuth();
  const [metrics, setMetrics] = useState<PipelineMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const labels = useMemo(
    () => ({
      title: locale === "ru" ? "Operational metrics" : "Operational metrics",
      description:
        locale === "ru"
          ? "Экспортный экран для защиты: latency, degraded rate, manual review, fallbacks и quality flags."
          : "Export-ready defense screen with latency, degraded rate, manual review, fallbacks, and quality flags.",
      reportTitle: locale === "ru" ? "Ключевые выводы" : "Key takeaways",
      bullet1:
        locale === "ru"
          ? "Показывает фактическую скорость обработки и p95 latency по текущему стеку."
          : "Shows actual processing speed and p95 latency on the current stack.",
      bullet2:
        locale === "ru"
          ? "Отдельно выносит degraded paths, fallback usage и долю кейсов, ушедших в ручную проверку."
          : "Highlights degraded paths, fallback usage, and the share of cases routed to manual review.",
      bullet3:
        locale === "ru"
          ? "Подходит как export/report screen для жюри без раскрытия внутренней админки."
          : "Works as an export/report screen for judges without exposing the full admin workflow.",
      loading: locale === "ru" ? "Загружаю operational metrics..." : "Loading operational metrics...",
    }),
    [locale],
  );

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.replace("/login");
      return;
    }
    if (user?.role === "admin") {
      void loadMetrics();
    }
  }, [authLoading, router, user]);

  async function loadMetrics() {
    setLoading(true);
    setError("");
    try {
      setMetrics(await adminApi.getPipelineMetrics(40));
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to load metrics");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header />
      <main className="min-w-0 px-5 py-6 lg:px-8 lg:py-8 pb-24">
        <div className="container-app page-shell">
          <div className="page-stack">
            <div className="card p-6">
              <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[800] tracking-tighter">
                {labels.title}
              </h1>
              <p className="mt-3 max-w-[62rem] text-[1rem] leading-relaxed text-muted">
                {labels.description}
              </p>
            </div>

            {loading ? (
              <div className="card p-12 text-center text-muted font-[700]">{labels.loading}</div>
            ) : error ? (
              <div className="card p-6 text-[var(--brand-coral)] font-[700]">{error}</div>
            ) : (
              <>
                <div className="card p-6">
                  <PipelineMetricsPanel metrics={metrics} locale={locale} mode="full" />
                </div>

                <div className="card p-6">
                  <div className="mb-4 text-[1rem] font-[800]">{labels.reportTitle}</div>
                  <ul className="space-y-3 text-[0.98rem] leading-relaxed text-muted-strong">
                    <li>{labels.bullet1}</li>
                    <li>{labels.bullet2}</li>
                    <li>{labels.bullet3}</li>
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
