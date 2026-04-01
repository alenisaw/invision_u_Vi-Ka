"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import DemoCard from "@/components/candidate/DemoCard";
import PipelineProgress from "@/components/candidate/PipelineProgress";
import { demoApi } from "@/lib/api";
import type { FixtureSummary } from "@/types";

const PIPELINE_STEP_COUNT = 7;
const STEP_INTERVAL_MS = 1800;

const SORT_OPTIONS = [
  { value: "az", label: "По алфавиту (А-Я)" },
  { value: "za", label: "По алфавиту (Я-А)" },
  { value: "program", label: "По программе" },
];

export default function CandidatesPage() {
  const router = useRouter();
  const [fixtures, setFixtures] = useState<FixtureSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("az");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const [runState, setRunState] = useState<{slug: string; status: "running" | "completed" | "error" | "idle"; step: number;} | null>(null);
  const stepTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    demoApi.listFixtures().then(setFixtures).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let result = [...fixtures];

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(f =>
        f.meta.display_name.toLowerCase().includes(q) ||
        f.meta.program.toLowerCase().includes(q)
      );
    }

    result.sort((a, b) => {
      if (sort === "az") {
        return a.meta.display_name.localeCompare(b.meta.display_name);
      }
      if (sort === "za") {
        return b.meta.display_name.localeCompare(a.meta.display_name);
      }
      if (sort === "program") {
        return a.meta.program.localeCompare(b.meta.program);
      }
      return 0;
    });

    return result;
  }, [fixtures, search, sort]);

  const handleRun = useCallback(async (slug: string) => {
    if (runState?.status === "running") return;
    setRunState({ slug, status: "running", step: 0 });
    let currentStep = 0;
    stepTimer.current = setInterval(() => {
      currentStep++;
      if (currentStep < PIPELINE_STEP_COUNT) setRunState(p => p ? {...p, step: currentStep} : p);
    }, STEP_INTERVAL_MS);

    try {
      const res = await demoApi.runFixture(slug);
      if (stepTimer.current) clearInterval(stepTimer.current);
      setRunState({ slug, status: "completed", step: PIPELINE_STEP_COUNT });
      setTimeout(() => router.push(`/dashboard/${res.candidate_id}`), 1200);
    } catch {
      if (stepTimer.current) clearInterval(stepTimer.current);
      setRunState({ slug, status: "error", step: 0 });
    }
  }, [router, runState?.status]);

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 min-w-0 p-6 lg:p-10 pb-24 relative">
          <div className="w-full">
            <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[800] mb-2 tracking-tighter">
              Пул кандидатов
            </h1>
            <p className="text-[1rem] mb-10 text-muted">
              Демонстрация полного пайплайна оценки. Выберите кандидата для тестирования.
            </p>

            {/* Сортировка */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-end gap-6 mb-6">
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="chip py-3 px-6 pr-16 font-[700] w-full lg:w-[280px] appearance-none outline-none cursor-pointer transition-all"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 1.5rem center',
                  backgroundSize: '1rem',
                }}
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            {/* Поиск и Переключатель вида */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Поиск по имени или программе..."
                className="flex-1 px-6 py-4 text-[1rem] font-[600] rounded-[1rem] bg-[var(--surface-subtle)] border border-[var(--brand-line)] outline-none focus:ring-2 focus:ring-[var(--brand-blue)]"
              />
              <div className="flex gap-1 p-1.5 rounded-[1.2rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] shrink-0 w-full sm:w-[320px]">
                <button onClick={() => setViewMode("grid")} className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${viewMode === "grid" ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg" : "text-muted hover:bg-[var(--surface-hover)]"}`}>Сетка</button>
                <button onClick={() => setViewMode("list")} className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${viewMode === "list" ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg" : "text-muted hover:bg-[var(--surface-hover)]"}`}>Строка</button>
              </div>
            </div>

            {/* Прогресс пайплайна */}
            {runState && (
              <div className="card card--dark p-6 mb-8 bg-[#181a1b] border border-[var(--brand-blue)]/30">
                <div className="text-[0.9rem] font-[700] text-[var(--brand-paper)] mb-4">
                  {runState.status === "running" ? `Обработка: ${fixtures.find(f => f.meta.slug === runState.slug)?.meta.display_name || "Кандидат"}...` : "Готово!"}
                </div>
                <PipelineProgress status={runState.status} currentStep={runState.step} />
              </div>
            )}

            {/* Сетка / Список */}
            <div className="w-full overflow-hidden">
              <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6" : "flex flex-col gap-4"}>
                {filtered.map((f) => {
                  const isProcessing = runState?.slug === f.meta.slug && runState.status === "running";
                  const isDisabled = runState?.status === "running" && runState.slug !== f.meta.slug;

                  return (
                    <div key={f.meta.slug} className="relative group h-full flex flex-col">
                      <div className="flex-1 transition-all duration-300 rounded-[1.2rem] flex flex-col">
                        <div className="flex-1 h-full">
                           <DemoCard
                             meta={f.meta}
                             onRun={handleRun}
                             viewMode={viewMode}
                             isRunning={isProcessing}
                             isDisabled={isDisabled}
                           />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {filtered.length === 0 && !loading && (
              <div className="text-center py-20 text-muted font-[700] text-[1.1rem]">
                Кандидаты не найдены
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
