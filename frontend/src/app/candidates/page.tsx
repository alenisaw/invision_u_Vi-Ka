"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import DemoCard from "@/components/candidate/DemoCard";
import PipelineProgress from "@/components/candidate/PipelineProgress";
import { demoApi } from "@/lib/api";
import type { FixtureSummary } from "@/types";

const PIPELINE_STEP_COUNT = 7;
const STEP_INTERVAL_MS = 1800;

type RunState = {
  slug: string;
  status: "running" | "completed" | "error";
  step: number;
  candidateId: string | null;
  error: string | null;
};

export default function CandidatesPage() {
  const router = useRouter();
  const [fixtures, setFixtures] = useState<FixtureSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterArchetype, setFilterArchetype] = useState<string>("all");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [runState, setRunState] = useState<RunState | null>(null);
  const stepTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    demoApi.listFixtures().then(setFixtures).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return fixtures.filter((f) => {
      const m = f.meta;
      const matchesSearch =
        !q ||
        m.display_name.toLowerCase().includes(q) ||
        m.program.toLowerCase().includes(q) ||
        m.description.toLowerCase().includes(q);
      const matchesArchetype = filterArchetype === "all" || m.archetype === filterArchetype;
      return matchesSearch && matchesArchetype;
    });
  }, [fixtures, search, filterArchetype]);

  const handleToggleSelect = useCallback((slug: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) {
        next.delete(slug);
      } else if (next.size < 3) {
        next.add(slug);
      }
      return next;
    });
  }, []);

  const handleRun = useCallback(
    async (slug: string) => {
      if (runState?.status === "running") return;

      setRunState({ slug, status: "running", step: 0, candidateId: null, error: null });

      let currentStep = 0;
      stepTimer.current = setInterval(() => {
        currentStep += 1;
        if (currentStep < PIPELINE_STEP_COUNT) {
          setRunState((prev) => (prev ? { ...prev, step: currentStep } : prev));
        }
      }, STEP_INTERVAL_MS);

      try {
        const result = await demoApi.runFixture(slug);
        if (stepTimer.current) clearInterval(stepTimer.current);
        setRunState({
          slug,
          status: "completed",
          step: PIPELINE_STEP_COUNT,
          candidateId: result.candidate_id,
          error: null,
        });
        setTimeout(() => {
          router.push(`/dashboard/${result.candidate_id}`);
        }, 1200);
      } catch (err) {
        if (stepTimer.current) clearInterval(stepTimer.current);
        setRunState((prev) => ({
          slug,
          status: "error",
          step: prev?.step ?? 0,
          candidateId: null,
          error: err instanceof Error ? err.message : "Pipeline error",
        }));
      }
    },
    [runState, router],
  );

  const handleCompare = () => {
    if (selected.size < 2) return;
    const slugs = Array.from(selected).join(",");
    router.push(`/candidates/compare?slugs=${slugs}`);
  };

  useEffect(() => {
    return () => {
      if (stepTimer.current) clearInterval(stepTimer.current);
    };
  }, []);

  const archetypes = ["all", "strong", "balanced", "weak", "risky", "incomplete"];
  const archetypeLabels: Record<string, string> = {
    all: "Все",
    strong: "Сильные",
    balanced: "Средние",
    weak: "Слабые",
    risky: "Риск",
    incomplete: "Неполные",
  };

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8">
          <div className="container-app">
            <h1
              className="text-[clamp(2rem,1.65rem+1.8vw,3.2rem)] font-[800] mb-2"
              style={{ letterSpacing: "-0.04em" }}
            >
              Пул кандидатов
            </h1>
            <p className="text-[0.95rem] mb-6" style={{ color: "var(--brand-muted)" }}>
              Предзагруженные анкеты для демонстрации полного пайплайна оценки
            </p>

            {/* Filters */}
            <div className="flex flex-wrap gap-3 mb-6 items-center">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск по имени или программе..."
                className="px-4 py-2.5 rounded-[1rem] text-[0.88rem] font-[500] outline-none flex-1 min-w-[200px]"
                style={{
                  border: "1px solid rgba(20, 20, 20, 0.1)",
                  background: "rgba(255, 255, 255, 0.82)",
                }}
              />
              <div className="flex gap-1.5">
                {archetypes.map((a) => (
                  <button
                    key={a}
                    onClick={() => setFilterArchetype(a)}
                    className="chip"
                    style={{
                      background:
                        filterArchetype === a
                          ? "var(--brand-ink)"
                          : "rgba(20, 20, 20, 0.05)",
                      color: filterArchetype === a ? "#fff" : "var(--brand-muted-strong)",
                    }}
                  >
                    {archetypeLabels[a]}
                  </button>
                ))}
              </div>
            </div>

            {/* Pipeline progress overlay */}
            {runState && (
              <div className="card card--dark p-5 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-[0.82rem] font-[700]" style={{ color: "#fff" }}>
                    {runState.status === "running"
                      ? `Обработка: ${fixtures.find((f) => f.meta.slug === runState.slug)?.meta.display_name ?? runState.slug}`
                      : runState.status === "completed"
                        ? "Готово! Переход к результатам..."
                        : `Ошибка: ${runState.error}`}
                  </div>
                  {runState.status === "error" && (
                    <button
                      onClick={() => setRunState(null)}
                      className="text-[0.78rem] font-[600]"
                      style={{ color: "rgba(255,255,255,0.6)" }}
                    >
                      Закрыть
                    </button>
                  )}
                </div>
                <PipelineProgress status={runState.status} currentStep={runState.step} />
              </div>
            )}

            {/* Cards grid */}
            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div
                    key={i}
                    className="card p-5 h-[220px] animate-pulse"
                    style={{ background: "rgba(20, 20, 20, 0.03)" }}
                  />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filtered.map((f) => (
                  <DemoCard
                    key={f.meta.slug}
                    meta={f.meta}
                    onRun={handleRun}
                    onToggleSelect={handleToggleSelect}
                    isRunning={runState?.slug === f.meta.slug && runState.status === "running"}
                    isSelected={selected.has(f.meta.slug)}
                    isDisabled={runState?.status === "running" && runState.slug !== f.meta.slug}
                  />
                ))}
              </div>
            )}

            {filtered.length === 0 && !loading && (
              <p className="text-center text-[0.92rem] font-[500] py-12" style={{ color: "var(--brand-muted)" }}>
                Кандидаты не найдены
              </p>
            )}
          </div>
        </main>
      </div>

      {/* Sticky compare footer */}
      {selected.size >= 2 && (
        <div
          className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-center gap-4 px-6 py-4"
          style={{
            background: "rgba(20, 20, 20, 0.95)",
            backdropFilter: "blur(12px)",
          }}
        >
          <span className="text-[0.88rem] font-[600]" style={{ color: "rgba(255,255,255,0.7)" }}>
            Выбрано {selected.size} из 3
          </span>
          <button onClick={handleCompare} className="btn" style={{ background: "var(--brand-blue)", color: "#000" }}>
            Сравнить кандидатов
          </button>
          <button
            onClick={() => setSelected(new Set())}
            className="text-[0.82rem] font-[600]"
            style={{ color: "rgba(255,255,255,0.5)" }}
          >
            Сбросить
          </button>
        </div>
      )}
    </>
  );
}
