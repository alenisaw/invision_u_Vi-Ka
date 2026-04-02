"use client";

import Link from "next/link";
import { useCallback, useState, type ReactNode } from "react";
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
      setForm((previous) => ({ ...previous, [key]: value }));
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
      setMessage(`Кандидат обработан и добавлен в список: ${result.pipeline_status}`);
      setTimeout(() => router.push(`/candidates?highlight=${result.candidate_id}`), 1500);
    } catch (err) {
      clearInterval(timer);
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Ошибка обработки");
    }
  }

  function handleFormSubmit() {
    if (!isFormValid) return;
    void runPipeline(buildPayload(form));
  }

  function handleJsonSubmit() {
    if (!jsonInput.trim()) return;
    try {
      void runPipeline(JSON.parse(jsonInput));
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

  function removeProject(index: number) {
    updateField(
      "project_descriptions",
      form.project_descriptions.filter((_, currentIndex) => currentIndex !== index),
    );
  }

  function updateProject(index: number, value: string) {
    updateField(
      "project_descriptions",
      form.project_descriptions.map((project, currentIndex) =>
        currentIndex === index ? value : project,
      ),
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
              Заполните анкету или вставьте JSON, чтобы запустить пайплайн оценки и
              добавить кандидата в список.
            </p>

            <div className="flex gap-2 mb-6">
              {(["form", "json"] as const).map((currentTab) => (
                <button
                  key={currentTab}
                  onClick={() => {
                    setTab(currentTab);
                    handleReset();
                  }}
                  className={`chip ${tab === currentTab ? "is-active" : ""}`}
                >
                  {currentTab === "form" ? "Анкета" : "JSON"}
                </button>
              ))}
            </div>

            {status !== "idle" && (
              <div className="card card--dark p-5 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-[0.82rem] font-[700]" style={{ color: "var(--brand-paper)" }}>
                    {status === "running"
                      ? "Обработка кандидата..."
                      : status === "completed"
                        ? "Готово. Перехожу к списку кандидатов..."
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
                    <Link
                      href={`/dashboard/${candidateId}`}
                      className="btn btn--sm"
                      style={{
                        background: "var(--brand-lime)",
                        color: "var(--brand-ink)",
                        borderColor: "var(--brand-lime)",
                      }}
                    >
                      Открыть рейтинг
                    </Link>
                    <Link
                      href={`/candidates?highlight=${candidateId}`}
                      className="btn btn--ghost btn--sm"
                      style={{ color: "var(--brand-paper)" }}
                    >
                      Перейти в список кандидатов
                    </Link>
                  </div>
                )}
              </div>
            )}

            {tab === "form" && (
              <>
                <FormSection title="Личные данные" required>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput label="Фамилия *" value={form.last_name} onChange={(value) => updateField("last_name", value)} placeholder="Ахметжанов" />
                    <FormInput label="Имя *" value={form.first_name} onChange={(value) => updateField("first_name", value)} placeholder="Данияр" />
                    <FormInput label="Отчество" value={form.patronymic} onChange={(value) => updateField("patronymic", value)} placeholder="Бахытжанович" />
                    <FormInput label="Дата рождения *" type="date" value={form.date_of_birth} onChange={(value) => updateField("date_of_birth", value)} />
                    <FormSelect
                      label="Пол"
                      value={form.gender}
                      onChange={(value) => updateField("gender", value)}
                      options={[
                        { value: "", label: "Не указан" },
                        { value: "male", label: "Мужской" },
                        { value: "female", label: "Женский" },
                      ]}
                    />
                    <FormInput label="Гражданство" value={form.citizenship} onChange={(value) => updateField("citizenship", value)} placeholder="KZ" />
                  </div>
                </FormSection>

                <FormSection title="Образование">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormSelect
                      label="Программа *"
                      value={form.selected_program}
                      onChange={(value) => updateField("selected_program", value)}
                      options={PROGRAMS.map((program) => ({ value: program, label: program }))}
                    />
                    <FormSelect
                      label="Языковой экзамен"
                      value={form.language_exam_type}
                      onChange={(value) => updateField("language_exam_type", value)}
                      options={EXAM_TYPES.map((exam) => ({
                        value: exam,
                        label: exam || "Не сдавал",
                      }))}
                    />
                    {form.language_exam_type && (
                      <FormInput
                        label="Бал"
                        type="number"
                        value={form.language_score}
                        onChange={(value) => updateField("language_score", value)}
                        placeholder="0.0 – 9.0"
                      />
                    )}
                  </div>
                </FormSection>

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
                        onChange={(event) => updateField("essay_text", event.target.value)}
                        placeholder="Напишите мотивационное эссе в 3–5 абзацах..."
                        rows={8}
                        className="px-4 py-3 text-[0.88rem] font-[500] resize-y"
                        style={{ lineHeight: 1.7 }}
                      />
                    </div>

                    <FormInput
                      label="Ссылка на видеоинтервью"
                      type="url"
                      value={form.video_url}
                      onChange={(value) => updateField("video_url", value)}
                      placeholder="https://..."
                    />

                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-[0.82rem] font-[700] text-muted-strong">Проекты</label>
                        <button
                          onClick={addProject}
                          className="text-[0.78rem] font-[700]"
                          style={{ color: "var(--brand-blue)" }}
                        >
                          + Добавить
                        </button>
                      </div>
                      <div className="flex flex-col gap-2">
                        {form.project_descriptions.map((project, index) => (
                          <div key={`${index}-${project}`} className="flex gap-2">
                            <input
                              type="text"
                              value={project}
                              onChange={(event) => updateProject(index, event.target.value)}
                              placeholder={`Проект ${index + 1}: краткое описание...`}
                              className="flex-1 px-4 py-2.5 text-[0.86rem] font-[500]"
                            />
                            {form.project_descriptions.length > 1 && (
                              <button
                                onClick={() => removeProject(index)}
                                className="text-[0.82rem] font-[600] px-2"
                                style={{ color: "var(--brand-coral)" }}
                              >
                                Удалить
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    <FormInput
                      label="Краткое описание опыта"
                      value={form.experience_summary}
                      onChange={(value) => updateField("experience_summary", value)}
                      placeholder="Опыт, навыки, достижения..."
                    />
                  </div>
                </FormSection>

                <CollapsibleSection title="Дополнительно">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput label="Телефон" value={form.phone} onChange={(value) => updateField("phone", value)} placeholder="+7..." />
                    <FormInput label="Telegram" value={form.telegram} onChange={(value) => updateField("telegram", value)} placeholder="@username" />
                    <div className="sm:col-span-2 flex items-center gap-3">
                      <label className="flex items-center gap-2 cursor-pointer text-[0.84rem] font-[600]">
                        <input
                          type="checkbox"
                          checked={form.has_social_benefit}
                          onChange={(event) => updateField("has_social_benefit", event.target.checked)}
                          className="accent-[var(--brand-blue)] w-4 h-4"
                        />
                        Социальный статус
                      </label>
                      {form.has_social_benefit && (
                        <input
                          type="text"
                          value={form.benefit_type}
                          onChange={(event) => updateField("benefit_type", event.target.value)}
                          placeholder="Тип льготы..."
                          className="flex-1 px-3 py-2 text-[0.84rem] font-[500]"
                        />
                      )}
                    </div>
                  </div>
                </CollapsibleSection>

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

            {tab === "json" && (
              <div className="card p-6 mb-6">
                <div className="eyebrow mb-4">JSON кандидата</div>
                <textarea
                  value={jsonInput}
                  onChange={(event) => {
                    setJsonInput(event.target.value);
                    handleReset();
                  }}
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

function FormSection({
  title,
  required,
  children,
}: {
  title: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="card p-5 mb-4">
      <div className="flex items-center gap-2 mb-4">
        <div className="eyebrow">{title}</div>
        {required && (
          <span
            className="text-[0.7rem] font-[700] px-1.5 py-0.5 rounded-full"
            style={{
              background: "var(--danger-soft-bg)",
              color: "var(--danger-soft-text)",
            }}
          >
            обязательно
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

function FormInput({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
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
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="px-4 py-2.5 text-[0.86rem] font-[500]"
        {...(type === "number" ? { step: "0.5", min: "0", max: "120" } : {})}
      />
    </div>
  );
}

function FormSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className="block text-[0.82rem] font-[700] mb-1.5 text-muted-strong">
        {label}
      </label>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="px-4 py-2.5 text-[0.86rem] font-[500]"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function CollapsibleSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="card p-5 mb-4">
      <button onClick={() => setOpen(!open)} className="flex items-center justify-between w-full">
        <div className="eyebrow">{title}</div>
        <span className="text-[0.82rem] font-[700] text-muted">{open ? "−" : "+"}</span>
      </button>
      {open && <div className="mt-4">{children}</div>}
    </div>
  );
}
