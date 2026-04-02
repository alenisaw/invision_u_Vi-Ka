"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import PipelineProgress from "@/components/candidate/PipelineProgress";
import CandidatePoolTable, {
  type CandidatePoolTableItem,
} from "@/components/candidate/CandidatePoolTable";
import StatusBadge from "@/components/dashboard/StatusBadge";
import { demoApi, reviewerApi } from "@/lib/api";
import { formatDate, formatPercent, localizeLabels } from "@/lib/utils";
import type { CandidateListItem, FixtureSummary } from "@/types";

const PIPELINE_STEP_COUNT = 7;
const STEP_INTERVAL_MS = 1800;

const SORT_OPTIONS = [
  { value: "recent", label: "Сначала новые" },
  { value: "rpi_desc", label: "По RPI" },
  { value: "name_asc", label: "По имени" },
  { value: "program_asc", label: "По программе" },
] as const;

type SortValue = (typeof SORT_OPTIONS)[number]["value"];
type ViewMode = "table" | "grid";

interface RunState {
  slug: string;
  status: "running" | "completed" | "error";
  step: number;
}

type CandidatePoolItem = CandidatePoolTableItem & {
  searchText: string;
};

function buildProcessedItem(candidate: CandidateListItem): CandidatePoolItem {
  return {
    id: candidate.candidate_id,
    kind: "processed",
    name: candidate.name,
    selectedProgram: candidate.selected_program,
    sourceLabel: "Загрузка",
    sourceTone: "lime",
    statusLabel: "Обработан",
    recommendationStatus: candidate.recommendation_status,
    reviewPriorityIndex: candidate.review_priority_index,
    confidence: candidate.confidence,
    tags: [...candidate.top_strengths, ...candidate.caution_flags].slice(0, 3),
    createdAt: candidate.created_at,
    actionLabel: "Просмотреть рейтинг",
    href: `/dashboard/${candidate.candidate_id}`,
    searchText: `${candidate.name} ${candidate.selected_program}`.toLowerCase(),
  };
}

function buildFixtureItem(fixture: FixtureSummary): CandidatePoolItem {
  return {
    id: `fixture:${fixture.meta.slug}`,
    kind: "fixture",
    name: fixture.meta.display_name,
    selectedProgram: fixture.meta.program,
    sourceLabel: "Демо",
    sourceTone: "blue",
    statusLabel: "Готов к запуску",
    reviewPriorityIndex: null,
    confidence: null,
    tags: [fixture.meta.language, "Тестовый сценарий"],
    createdAt: null,
    actionLabel: "Добавить в очередь",
    runSlug: fixture.meta.slug,
    searchText: `${fixture.meta.display_name} ${fixture.meta.program} ${fixture.meta.language}`.toLowerCase(),
  };
}

export default function CandidatesPage() {
  return (
    <Suspense fallback={<CandidatesPageFallback />}>
      <CandidatesPageInner />
    </Suspense>
  );
}

function CandidatesPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const highlightId = searchParams.get("highlight");

  const [processedCandidates, setProcessedCandidates] = useState<CandidateListItem[]>([]);
  const [fixtures, setFixtures] = useState<FixtureSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortValue>("recent");
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [sourceFilter, setSourceFilter] = useState<"all" | "processed" | "fixture">("all");

  const [runState, setRunState] = useState<RunState | null>(null);
  const stepTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError("");

      try {
        const [dashboardCandidates, demoFixtures] = await Promise.all([
          reviewerApi.listDashboardCandidates(),
          demoApi.listFixtures(),
        ]);
        setProcessedCandidates(dashboardCandidates);
        setFixtures(demoFixtures);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Не удалось загрузить список кандидатов");
      } finally {
        setLoading(false);
      }
    }

    void loadData();
  }, []);

  useEffect(() => {
    return () => {
      if (stepTimer.current) {
        clearInterval(stepTimer.current);
      }
    };
  }, []);

  const items = useMemo(() => {
    const combined = [
      ...processedCandidates.map(buildProcessedItem),
      ...fixtures.map(buildFixtureItem),
    ];

    const query = search.trim().toLowerCase();
    let filtered = combined.filter((item) => {
      if (sourceFilter !== "all" && item.kind !== sourceFilter) {
        return false;
      }

      if (!query) {
        return true;
      }

      return item.searchText.includes(query);
    });

    filtered = filtered.sort((left, right) => {
      if (highlightId) {
        if (left.id === highlightId && right.id !== highlightId) return -1;
        if (right.id === highlightId && left.id !== highlightId) return 1;
      }

      switch (sort) {
        case "name_asc":
          return left.name.localeCompare(right.name, "ru");
        case "program_asc":
          return left.selectedProgram.localeCompare(right.selectedProgram, "ru");
        case "rpi_desc":
          return (right.reviewPriorityIndex ?? -1) - (left.reviewPriorityIndex ?? -1);
        case "recent":
        default:
          return new Date(right.createdAt ?? 0).getTime() - new Date(left.createdAt ?? 0).getTime();
      }
    });

    return filtered;
  }, [fixtures, highlightId, processedCandidates, search, sort, sourceFilter]);

  const stats = useMemo(
    () => ({
      total: items.length,
      processed: processedCandidates.length,
      fixtures: fixtures.length,
    }),
    [fixtures.length, items.length, processedCandidates.length],
  );

  const handleRunFixture = useCallback(
    async (slug: string) => {
      if (runState?.status === "running") {
        return;
      }

      setRunState({ slug, status: "running", step: 0 });
      let currentStep = 0;
      stepTimer.current = setInterval(() => {
        currentStep += 1;
        if (currentStep < PIPELINE_STEP_COUNT) {
          setRunState((previous) => (previous ? { ...previous, step: currentStep } : previous));
        }
      }, STEP_INTERVAL_MS);

      try {
        const result = await demoApi.runFixture(slug);
        if (stepTimer.current) clearInterval(stepTimer.current);
        setRunState({ slug, status: "completed", step: PIPELINE_STEP_COUNT });
        setTimeout(() => router.push(`/dashboard/${result.candidate_id}`), 1200);
      } catch {
        if (stepTimer.current) clearInterval(stepTimer.current);
        setRunState({ slug, status: "error", step: 0 });
      }
    },
    [router, runState?.status],
  );

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 min-w-0 p-6 lg:p-10 pb-24 relative">
          <div className="w-full">
            <h1 className="text-[clamp(2.2rem,2rem+2vw,3.5rem)] font-[800] mb-2 tracking-tighter">
              Список кандидатов
            </h1>
            <p className="text-[1rem] mb-10 text-muted max-w-[72ch]">
              Здесь собраны кандидаты, уже прошедшие обработку через загрузку, и
              демо-сценарии для быстрого запуска пайплайна. По умолчанию открыт
              табличный вид, карточки можно вернуть в один клик.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              <StatCard label="Всего в списке" value={String(stats.total)} tone="lime" />
              <StatCard label="Обработанные" value={String(stats.processed)} tone="blue" />
              <StatCard label="Готовы к запуску" value={String(stats.fixtures)} tone="neutral" />
            </div>

            <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4 mb-6">
              <div className="flex flex-wrap gap-2">
                <FilterChip
                  active={sourceFilter === "all"}
                  onClick={() => setSourceFilter("all")}
                  label="Все"
                />
                <FilterChip
                  active={sourceFilter === "processed"}
                  onClick={() => setSourceFilter("processed")}
                  label="После обработки"
                />
                <FilterChip
                  active={sourceFilter === "fixture"}
                  onClick={() => setSourceFilter("fixture")}
                  label="Демо-сценарии"
                />
              </div>

              <select
                value={sort}
                onChange={(event) => setSort(event.target.value as SortValue)}
                className="chip py-3 px-6 pr-16 font-[700] w-full xl:w-[240px] appearance-none outline-none cursor-pointer transition-all"
                style={{
                  backgroundImage:
                    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E\")",
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 1.5rem center",
                  backgroundSize: "1rem",
                }}
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Поиск по имени, программе или типу кандидата..."
                className="flex-1 px-6 py-4 text-[1rem] font-[600] rounded-[1rem] bg-[var(--surface-subtle)] border border-[var(--brand-line)] outline-none focus:ring-2 focus:ring-[var(--brand-blue)]"
              />
              <div className="flex gap-1 p-1.5 rounded-[1.2rem] border border-[var(--brand-line)] bg-[var(--surface-subtle)] shrink-0 w-full sm:w-[320px]">
                <button
                  onClick={() => setViewMode("table")}
                  className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${
                    viewMode === "table"
                      ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg"
                      : "text-muted hover:bg-[var(--surface-hover)]"
                  }`}
                >
                  Таблица
                </button>
                <button
                  onClick={() => setViewMode("grid")}
                  className={`flex-1 py-2.5 rounded-[0.9rem] text-[0.9rem] font-[700] transition-all ${
                    viewMode === "grid"
                      ? "bg-[var(--brand-ink)] text-[var(--brand-paper)] shadow-lg"
                      : "text-muted hover:bg-[var(--surface-hover)]"
                  }`}
                >
                  Сетка
                </button>
              </div>
            </div>

            {runState && (
              <div className="card card--dark p-6 mb-8 bg-[#181a1b] border border-[var(--brand-blue)]/30">
                <div className="text-[0.9rem] font-[700] text-[var(--brand-paper)] mb-4">
                  {runState.status === "running"
                    ? `В обработке: ${
                        fixtures.find((fixture) => fixture.meta.slug === runState.slug)?.meta.display_name ??
                        "кандидат"
                      }`
                    : runState.status === "completed"
                      ? "Кандидат обработан, открываю рейтинг..."
                      : "Не удалось запустить обработку. Проверьте данные и попробуйте снова."}
                </div>
                <PipelineProgress status={runState.status} currentStep={runState.step} />
              </div>
            )}

            {error && (
              <div className="card p-5 mb-8 border border-[var(--brand-coral)]/25 bg-[var(--brand-coral)]/8">
                <div className="text-[0.95rem] font-[700] text-[var(--brand-coral)]">
                  {error}
                </div>
              </div>
            )}

            {loading ? (
              <div className="card p-12 text-center text-muted font-[700]">
                Загружаю список кандидатов...
              </div>
            ) : viewMode === "table" ? (
              <CandidatePoolTable
                items={items}
                highlightedId={highlightId}
                runningSlug={runState?.status === "running" ? runState.slug : null}
                onRunFixture={handleRunFixture}
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {items.map((item) => {
                  const isHighlighted = highlightId === item.id;
                  const isRunning = Boolean(
                    item.runSlug && runState?.status === "running" && runState.slug === item.runSlug,
                  );
                  const localizedTags = localizeLabels(item.tags.slice(0, 3));

                  return (
                    <div
                      key={item.id}
                      className="card p-6 flex flex-col transition-all duration-300"
                      style={{
                        outline: isHighlighted ? "3px solid var(--brand-blue)" : "none",
                        outlineOffset: "-3px",
                      }}
                    >
                      <div className="flex items-start justify-between gap-4 mb-4">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <span
                              className={`badge ${
                                item.sourceTone === "lime"
                                  ? "badge--lime"
                                  : item.sourceTone === "blue"
                                    ? "badge--blue"
                                    : "badge--neutral"
                              }`}
                            >
                              {item.sourceLabel}
                            </span>
                            {item.recommendationStatus ? (
                              <StatusBadge status={item.recommendationStatus} />
                            ) : (
                              <span className="badge badge--neutral">{item.statusLabel}</span>
                            )}
                          </div>
                          <h3 className="text-[1.15rem] font-[900] leading-tight tracking-tight">
                            {item.name}
                          </h3>
                        </div>
                      </div>

                      <p className="text-[0.9rem] text-muted line-clamp-2 mb-5 h-[2.8rem] leading-relaxed">
                        {item.selectedProgram}
                      </p>

                      <div className="grid grid-cols-2 gap-3 mb-5">
                        <MetricCard
                          label="RPI"
                          value={
                            item.reviewPriorityIndex != null
                              ? formatPercent(item.reviewPriorityIndex)
                              : "—"
                          }
                        />
                        <MetricCard
                          label="Уверенность"
                          value={item.confidence != null ? formatPercent(item.confidence) : "—"}
                        />
                      </div>

                      <div className="flex flex-wrap gap-2 mb-6 min-h-[2.5rem]">
                        {localizedTags.length > 0 ? (
                          localizedTags.map((tag) => (
                            <span key={`${item.id}-${tag}`} className="badge badge--neutral">
                              {tag}
                            </span>
                          ))
                        ) : (
                          <span className="text-[0.82rem] text-muted">Метки появятся после обработки</span>
                        )}
                      </div>

                      <div className="mt-auto pt-5 flex items-center justify-between border-t border-[var(--brand-line)] gap-3">
                        <span className="text-[0.8rem] font-[700] text-muted font-numbers">
                          {item.createdAt ? formatDate(item.createdAt) : "Без даты"}
                        </span>
                        {item.href ? (
                          <Link href={item.href} className="btn btn--sm btn--dark">
                            {item.actionLabel}
                          </Link>
                        ) : (
                          <button
                            onClick={() => item.runSlug && handleRunFixture(item.runSlug)}
                            disabled={!item.runSlug || Boolean(isRunning)}
                            className="btn btn--sm btn--dark disabled:opacity-50 disabled:cursor-wait"
                          >
                            {isRunning ? "В обработке..." : item.actionLabel}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {!loading && items.length === 0 && (
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

function CandidatesPageFallback() {
  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 min-w-0 p-6 lg:p-10 pb-24 relative">
          <div className="card p-12 text-center text-muted font-[700]">
            Загружаю список кандидатов...
          </div>
        </main>
      </div>
    </>
  );
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "lime" | "blue" | "neutral";
}) {
  const background =
    tone === "lime"
      ? "rgba(193, 241, 29, 0.16)"
      : tone === "blue"
        ? "rgba(61, 237, 241, 0.14)"
        : "var(--surface-subtle)";

  return (
    <div className="rounded-[1.2rem] px-6 py-6 bg-[var(--surface-subtle)]" style={{ background }}>
      <div className="text-[0.75rem] font-[700] uppercase tracking-[0.12em] mb-2 text-muted">
        {label}
      </div>
      <div className="text-[1.7rem] font-[800] font-numbers">{value}</div>
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button onClick={onClick} className={`chip ${active ? "is-active" : ""}`}>
      {label}
    </button>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1rem] p-4 bg-[var(--surface-subtle-2)]">
      <div className="text-[0.7rem] font-[800] uppercase text-muted mb-1 tracking-widest">
        {label}
      </div>
      <div className="text-[1.2rem] font-[800] font-numbers">{value}</div>
    </div>
  );
}
