"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import PipelineProgress from "@/components/candidate/PipelineProgress";
import { pipelineApi } from "@/lib/api";

type Tab = "form" | "json";

const PROGRAMS = [
  "Цифровые медиа и маркетинг",
  "Инновационные цифровые продукты и сервисы",
  "Креативная инженерия",
  "Социология инноваций и лидерства",
  "Стратегии государственного управления и развития",
  "General Admissions",
];

const EXAM_TYPES = ["IELTS", "TOEFL", "Kaztest", ""];

interface FormState {
  first_name: string;
  last_name: string;
  patronymic: string;
  date_of_birth: string;
  gender: string;
  citizenship: string;
  selected_program: string;
  language_exam_type: string;
  language_score: string;
  essay_text: string;
  video_url: string;
  project_descriptions: string[];
  experience_summary: string;
  phone: string;
  telegram: string;
  has_social_benefit: boolean;
  benefit_type: string;
}

const INITIAL_FORM: FormState = {
  first_name: "",
  last_name: "",
  patronymic: "",
  date_of_birth: "",
  gender: "",
  citizenship: "KZ",
  selected_program: PROGRAMS[0],
  language_exam_type: "IELTS",
  language_score: "",
  essay_text: "",
  video_url: "",
  project_descriptions: [""],
  experience_summary: "",
  phone: "",
  telegram: "",
  has_social_benefit: false,
  benefit_type: "",
};

const PIPELINE_STEP_COUNT = 7;
const STEP_INTERVAL_MS = 1800;

function buildPayload(form: FormState): Record<string, unknown> {
  return {
    personal: {
      first_name: form.first_name,
      last_name: form.last_name,
      ...(form.patronymic ? { patronymic: form.patronymic } : {}),
      date_of_birth: form.date_of_birth,
      ...(form.gender ? { gender: form.gender } : {}),
      ...(form.citizenship ? { citizenship: form.citizenship } : {}),
    },
    contacts: {
      ...(form.phone ? { phone: form.phone } : {}),
      ...(form.telegram ? { telegram: form.telegram } : {}),
    },
    academic: {
      selected_program: form.selected_program,
      ...(form.language_exam_type ? { language_exam_type: form.language_exam_type } : {}),
      ...(form.language_score ? { language_score: parseFloat(form.language_score) } : {}),
    },
    content: {
      ...(form.essay_text ? { essay_text: form.essay_text } : {}),
      ...(form.video_url ? { video_url: form.video_url } : {}),
      project_descriptions: form.project_descriptions.filter(Boolean),
      ...(form.experience_summary ? { experience_summary: form.experience_summary } : {}),
    },
    social_status: {
      has_social_benefit: form.has_social_benefit,
      ...(form.has_social_benefit && form.benefit_type ? { benefit_type: form.benefit_type } : {}),
    },
  };
}

function wordCount(text: string): number {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

export default function UploadPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("form");
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [jsonInput, setJsonInput] = useState("");
  const [showPreview, setShowPreview] = useState(false);

  const [status, setStatus] = useState<"idle" | "running" | "completed" | "error">("idle");
  const [pipelineStep, setPipelineStep] = useState(0);
  const [message, setMessage] = useState("");
  const [candidateId, setCandidateId] = useState("");

  const updateField = useCallback(
    <K extends keyof FormState>(key: K, value: FormState[K]) => {
      setForm((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const isFormValid =
    form.first_name.trim() &&
    form.last_name.trim() &&
    form.date_of_birth &&
    form.selected_program;

  async function runPipeline(payload: unknown) {
    setStatus("running");
    setPipelineStep(0);
    setCandidateId("");
    setMessage("");

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep += 1;
      if (currentStep < PIPELINE_STEP_COUNT) {
        setPipelineStep(currentStep);
      }
    }, STEP_INTERVAL_MS);

    try {
      const result = await pipelineApi.submitCandidate(payload);
      clearInterval(timer);
      setPipelineStep(PIPELINE_STEP_COUNT);
      setStatus("completed");
      setCandidateId(result.candidate_id);
      setMessage(`Пайплайн завершён: ${result.pipeline_status}`);
      setTimeout(() => router.push(`/dashboard/${result.candidate_id}`), 1500);
    } catch (err) {
      clearInterval(timer);
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Ошибка обработки");
    }
  }

  function handleFormSubmit() {
    if (!isFormValid) return;
    runPipeline(buildPayload(form));
  }

  function handleJsonSubmit() {
    if (!jsonInput.trim()) return;
    try {
      runPipeline(JSON.parse(jsonInput));
    } catch {
      setStatus("error");
      setMessage("Неверный формат JSON");
    }
  }

  function handleReset() {
    setStatus("idle");
    setMessage("");
    setCandidateId("");
    setPipelineStep(0);
  }

  function addProject() {
    updateField("project_descriptions", [...form.project_descriptions, ""]);
  }

  function removeProject(idx: number) {
    updateField(
      "project_descriptions",
      form.project_descriptions.filter((_, i) => i !== idx),
    );
  }

  function updateProject(idx: number, value: string) {
    updateField(
      "project_descriptions",
      form.project_descriptions.map((p, i) => (i === idx ? value : p)),
    );
  }

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8">
          <div className="container-app max-w-4xl">
            <h1
              className="text-[clamp(2rem,1.65rem+1.8vw,3.2rem)] font-[800] mb-2"
              style={{ letterSpacing: "-0.04em" }}
            >
              Загрузка кандидата
            </h1>
            <p className="text-[0.95rem] mb-6 text-muted">
              Заполните анкету или загрузите JSON для запуска пайплайна оценки
            </p>

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
              {(["form", "json"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => { setTab(t); handleReset(); }}
                  className={`chip ${tab === t ? "is-active" : ""}`}
                >
                  {t === "form" ? "Анкета" : "JSON"}
                </button>
              ))}
            </div>

            {/* Pipeline progress */}
            {status !== "idle" && (
              <div className="card card--dark p-5 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-[0.82rem] font-[700]" style={{ color: "var(--brand-paper)" }}>
                    {status === "running"
                      ? "Обработка кандидата..."
                      : status === "completed"
                        ? "Готово! Переход к результатам..."
                        : `Ошибка: ${message}`}
                  </div>
                  {(status === "error" || status === "completed") && (
                    <button
                      onClick={handleReset}
                      className="text-[0.78rem] font-[600]"
                      style={{ color: "rgba(255,255,255,0.6)" }}
                    >
                      Закрыть
                    </button>
                  )}
                </div>
                <PipelineProgress status={status} currentStep={pipelineStep} />
                {status === "completed" && candidateId && (
                  <div className="flex gap-3 mt-4">
                    <Link href={`/dashboard/${candidateId}`} className="btn btn--sm" style={{ background: "var(--brand-lime)", color: "var(--brand-ink)", borderColor: "var(--brand-lime)" }}>
                      Открыть карточку
                    </Link>
                    <Link href="/dashboard" className="btn btn--ghost btn--sm" style={{ color: "var(--brand-paper)" }}>
                      Перейти в рейтинг
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* === FORM TAB === */}
            {tab === "form" && (
              <>
                {/* Section 1: Personal */}
                <FormSection title="Личные данные" required>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput label="Фамилия *" value={form.last_name} onChange={(v) => updateField("last_name", v)} placeholder="Ахметжанов"/>
                    <FormInput label="Имя *" value={form.first_name} onChange={(v) => updateField("first_name", v)} placeholder="Данияр" />
                    <FormInput label="Отчество" value={form.patronymic} onChange={(v) => updateField("patronymic", v)} placeholder="Бахытжанович" />
                    <FormInput label="Дата рождения *" type="date" value={form.date_of_birth} onChange={(v) => updateField("date_of_birth", v)} />
                    <FormSelect label="Пол" value={form.gender} onChange={(v) => updateField("gender", v)} options={[
                      { value: "", label: "Не указан" },
                      { value: "male", label: "Мужской" },
                      { value: "female", label: "Женский" },
                    ]} />
                    <FormInput label="Гражданство" value={form.citizenship} onChange={(v) => updateField("citizenship", v)} placeholder="KZ" />
                  </div>
                </FormSection>

                {/* Section 2: Academic */}
                <FormSection title="Образование">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormSelect label="Программа *" value={form.selected_program} onChange={(v) => updateField("selected_program", v)} options={PROGRAMS.map((p) => ({ value: p, label: p }))} />
                    <FormSelect label="Языковой экзамен" value={form.language_exam_type} onChange={(v) => updateField("language_exam_type", v)} options={EXAM_TYPES.map((t) => ({ value: t, label: t || "Не сдавал" }))} />
                    {form.language_exam_type && (
                      <FormInput label="Балл" type="number" value={form.language_score} onChange={(v) => updateField("language_score", v)} placeholder="0.0 – 9.0" />
                    )}
                  </div>
                </FormSection>

                {/* Section 3: Content */}
                <FormSection title="Контент">
                  <div className="flex flex-col gap-4">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-[0.82rem] font-[700] text-muted-strong">Эссе</label>
                        <span className="text-[0.76rem] font-[600] text-muted">
                          {wordCount(form.essay_text)} слов
                        </span>
                      </div>
                      <textarea
                        value={form.essay_text}
                        onChange={(e) => updateField("essay_text", e.target.value)}
                        placeholder="Напишите мотивационное эссе (3–5 абзацев)..."
                        rows={8}
                        className="px-4 py-3 text-[0.88rem] font-[500] resize-y"
                        style={{ lineHeight: 1.7 }}
                      />
                    </div>
                    <FormInput label="Ссылка на видео-интервью" type="url" value={form.video_url} onChange={(v) => updateField("video_url", v)} placeholder="https://..." />
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-[0.82rem] font-[700] text-muted-strong">Проекты</label>
                        <button onClick={addProject} className="text-[0.78rem] font-[700]" style={{ color: "var(--brand-blue)" }}>+ Добавить</button>
                      </div>
                      <div className="flex flex-col gap-2">
                        {form.project_descriptions.map((p, i) => (
                          <div key={i} className="flex gap-2">
                            <input
                              type="text"
                              value={p}
                              onChange={(e) => updateProject(i, e.target.value)}
                              placeholder={`Проект ${i + 1}: описание...`}
                              className="flex-1 px-4 py-2.5 text-[0.86rem] font-[500]"
                            />
                            {form.project_descriptions.length > 1 && (
                              <button onClick={() => removeProject(i)} className="text-[0.82rem] font-[600] px-2" style={{ color: "var(--brand-coral)" }}>×</button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                    <FormInput label="Краткое описание опыта" value={form.experience_summary} onChange={(v) => updateField("experience_summary", v)} placeholder="Опыт, навыки, достижения..." />
                  </div>
                </FormSection>

                {/* Section 4: Optional */}
                <CollapsibleSection title="Дополнительно (необязательно)">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput label="Телефон" value={form.phone} onChange={(v) => updateField("phone", v)} placeholder="+7..." />
                    <FormInput label="Telegram" value={form.telegram} onChange={(v) => updateField("telegram", v)} placeholder="@username" />
                    <div className="sm:col-span-2 flex items-center gap-3">
                      <label className="flex items-center gap-2 cursor-pointer text-[0.84rem] font-[600]">
                        <input
                          type="checkbox"
                          checked={form.has_social_benefit}
                          onChange={(e) => updateField("has_social_benefit", e.target.checked)}
                          className="accent-[var(--brand-blue)] w-4 h-4"
                        />
                        Социальный статус
                      </label>
                      {form.has_social_benefit && (
                        <input
                          type="text"
                          value={form.benefit_type}
                          onChange={(e) => updateField("benefit_type", e.target.value)}
                          placeholder="Тип льготы..."
                          className="flex-1 px-3 py-2 text-[0.84rem] font-[500]"
                        />
                      )}
                    </div>
                  </div>
                </CollapsibleSection>

                {/* Preview JSON toggle */}
                <div className="mt-4 mb-2">
                  <button
                    onClick={() => setShowPreview(!showPreview)}
                    className="text-[0.82rem] font-[700] text-muted"
                  >
                    {showPreview ? "Скрыть JSON" : "Показать JSON"}
                  </button>
                  {showPreview && (
                    <pre
                      className="mt-2 px-4 py-3 rounded-[1rem] text-[0.78rem] font-mono overflow-x-auto max-h-[300px] overflow-y-auto"
                      style={{ background: "var(--surface-subtle)", border: "1px solid var(--brand-line)" }}
                    >
                      {JSON.stringify(buildPayload(form), null, 2)}
                    </pre>
                  )}
                </div>

                {/* Submit */}
                <div className="flex gap-3 mt-4 mb-8">
                  <button
                    onClick={handleFormSubmit}
                    disabled={!isFormValid || status === "running"}
                    data-testid="submit-candidate-button"
                    className="btn btn--dark disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Отправить на оценку
                  </button>
                </div>
              </>
            )}

            {/* === JSON TAB === */}
            {tab === "json" && (
              <div className="card p-6 mb-6">
                <div className="eyebrow mb-4">JSON-данные кандидата</div>
                <textarea
                  value={jsonInput}
                  onChange={(e) => { setJsonInput(e.target.value); handleReset(); }}
                  placeholder={`{
  "personal": { "last_name": "...", "first_name": "...", "date_of_birth": "2007-01-01" },
  "academic": { "selected_program": "..." },
  "content": { "essay_text": "...", "video_url": "..." }
}`}
                  rows={16}
                  data-testid="candidate-json-input"
                  className="px-4 py-3 text-[0.88rem] font-[500] resize-y font-mono"
                  style={{ lineHeight: 1.6 }}
                />
                <div className="flex gap-3 mt-5">
                  <button
                    onClick={handleJsonSubmit}
                    disabled={!jsonInput.trim() || status === "running"}
                    data-testid="submit-json-button"
                    className="btn btn--dark disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Отправить
                  </button>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}

/* ---------- Reusable form sub-components ---------- */

function FormSection({ title, required, children }: { title: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="card p-5 mb-4">
      <div className="flex items-center gap-2 mb-4">
        <div className="eyebrow">{title}</div>
        {required && <span className="text-[0.7rem] font-[700] px-1.5 py-0.5 rounded-full" style={{ background: "var(--danger-soft-bg)", color: "var(--danger-soft-text)" }}>обязательно</span>}
      </div>
      {children}
    </div>
  );
}

function FormInput({ label, value, onChange, type = "text", placeholder }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-[0.82rem] font-[700] mb-1.5 text-muted-strong">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="px-4 py-2.5 text-[0.86rem] font-[500]"
        {...(type === "number" ? { step: "0.5", min: "0", max: "120" } : {})}
      />
    </div>
  );
}

function FormSelect({ label, value, onChange, options }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className="block text-[0.82rem] font-[700] mb-1.5 text-muted-strong">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="px-4 py-2.5 text-[0.86rem] font-[500]"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

function CollapsibleSection({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card p-5 mb-4">
      <button onClick={() => setOpen(!open)} className="flex items-center justify-between w-full">
        <div className="eyebrow">{title}</div>
        <span className="text-[0.82rem] font-[700] text-muted">
          {open ? "−" : "+"}
        </span>
      </button>
      {open && <div className="mt-4">{children}</div>}
    </div>
  );
}