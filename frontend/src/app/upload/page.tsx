"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import PipelineProgress from "@/components/candidate/PipelineProgress";
import DemoCard from "@/components/candidate/DemoCard";
import { useLocale } from "@/components/providers/LocaleProvider";
import { demoApi, pipelineApi } from "@/lib/api";
import { getProgramOptions } from "@/lib/i18n";
import type { FixtureSummary } from "@/types";

type Tab = "form" | "json" | "demo";

const EXAM_TYPES = ["IELTS", "TOEFL", "Kaztest", ""] as const;
const PIPELINE_STEP_COUNT = 7;
const STEP_INTERVAL_MS = 1800;

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
  email: string;
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
  selected_program: "Цифровые медиа и маркетинг",
  language_exam_type: "IELTS",
  language_score: "",
  essay_text: "",
  video_url: "",
  email: "",
  phone: "",
  telegram: "",
  has_social_benefit: false,
  benefit_type: "",
};

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
      email: form.email,
      ...(form.phone ? { phone: form.phone } : {}),
      ...(form.telegram ? { telegram: form.telegram } : {}),
    },
    academic: {
      selected_program: form.selected_program,
      ...(form.language_exam_type ? { language_exam_type: form.language_exam_type } : {}),
      ...(form.language_score ? { language_score: parseFloat(form.language_score) } : {}),
    },
    content: {
      video_url: form.video_url,
      ...(form.essay_text ? { essay_text: form.essay_text } : {}),
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
  const { locale, t } = useLocale();

  const [tab, setTab] = useState<Tab>("form");
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [jsonInput, setJsonInput] = useState("");
  const [showPreview, setShowPreview] = useState(false);
  const [fixtures, setFixtures] = useState<FixtureSummary[]>([]);
  const [fixturesLoading, setFixturesLoading] = useState(true);
  const [runningDemoSlug, setRunningDemoSlug] = useState<string | null>(null);

  const [status, setStatus] = useState<"idle" | "running" | "completed" | "error">("idle");
  const [pipelineStep, setPipelineStep] = useState(0);
  const [message, setMessage] = useState("");
  const [candidateId, setCandidateId] = useState("");

  useEffect(() => {
    async function loadFixtures() {
      try {
        const data = await demoApi.listFixtures();
        setFixtures(data);
      } finally {
        setFixturesLoading(false);
      }
    }

    void loadFixtures();
  }, []);

  const programOptions = useMemo(() => getProgramOptions(locale), [locale]);

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
    form.selected_program &&
    form.email.trim() &&
    form.video_url.trim();

  async function runPipeline(payload: unknown, demoSlug?: string) {
    setStatus("running");
    setPipelineStep(0);
    setCandidateId("");
    setMessage("");
    setRunningDemoSlug(demoSlug ?? null);

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
      setMessage(result.pipeline_status);
      setTimeout(() => router.push(`/candidates?highlight=${result.candidate_id}`), 1500);
    } catch (err) {
      clearInterval(timer);
      setStatus("error");
      setMessage(err instanceof Error ? err.message : t("pipeline.failed"));
    } finally {
      setRunningDemoSlug(null);
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
      setMessage(t("upload.json.invalid"));
    }
  }

  async function handleRunFixture(slug: string) {
    const fixture = fixtures.find((item) => item.meta.slug === slug);
    if (!fixture || runningDemoSlug) return;
    const detail = await demoApi.getFixture(slug);
    void runPipeline(detail.payload, slug);
  }

  function handleReset() {
    setStatus("idle");
    setMessage("");
    setCandidateId("");
    setPipelineStep(0);
    setRunningDemoSlug(null);
  }

  return (
    <>
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8 pb-20">
          <div className="container-app max-w-6xl">
            <section className="rounded-[2rem] border px-6 py-8 lg:px-8 lg:py-10 mb-8 page-glow">
              <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
                <div className="max-w-[56rem]">
                  <div className="eyebrow mb-3">{t("nav.upload")}</div>
                  <h1 className="text-[clamp(2.2rem,1.9rem+2vw,3.8rem)] font-[900] tracking-[-0.05em] mb-3">
                    {t("upload.title")}
                  </h1>
                  <p className="text-[1rem] text-muted leading-relaxed max-w-[72ch]">
                    {t("upload.description")}
                  </p>
                </div>
                <div className="rounded-[1.4rem] px-5 py-4 bg-[var(--surface-subtle)] border border-[var(--brand-line)] max-w-[24rem]">
                  <div className="text-[0.74rem] font-[800] uppercase tracking-[0.14em] text-muted mb-2">
                    ASR-first flow
                  </div>
                  <p className="text-[0.9rem] leading-relaxed text-muted-strong">
                    {t("upload.videoHint")}
                  </p>
                </div>
              </div>
            </section>

            <div className="flex gap-2 mb-6 flex-wrap">
              {(["form", "json", "demo"] as const).map((currentTab) => (
                <button
                  key={currentTab}
                  onClick={() => {
                    setTab(currentTab);
                    handleReset();
                  }}
                  className={`chip ${tab === currentTab ? "is-active" : ""}`}
                >
                  {currentTab === "form"
                    ? t("upload.tab.form")
                    : currentTab === "json"
                      ? t("upload.tab.json")
                      : t("upload.tab.demo")}
                </button>
              ))}
            </div>

            {status !== "idle" && (
              <div className="card card--dark p-5 mb-6">
                <div className="flex items-center justify-between mb-3 gap-3">
                  <div className="text-[0.82rem] font-[700]" style={{ color: "var(--brand-paper)" }}>
                    {status === "running"
                      ? t("pipeline.running")
                      : status === "completed"
                        ? t("pipeline.completed")
                        : `${t("pipeline.failed")}: ${message}`}
                  </div>
                  {(status === "error" || status === "completed") && (
                    <button
                      onClick={handleReset}
                      className="text-[0.78rem] font-[600]"
                      style={{ color: "rgba(255,255,255,0.6)" }}
                    >
                      {t("common.close")}
                    </button>
                  )}
                </div>
                <PipelineProgress status={status} currentStep={pipelineStep} />
                {status === "completed" && candidateId && (
                  <div className="flex gap-3 mt-4 flex-wrap">
                    <Link
                      href={`/dashboard/${candidateId}`}
                      className="btn btn--sm"
                      style={{
                        background: "var(--brand-lime)",
                        color: "var(--brand-ink)",
                        borderColor: "var(--brand-lime)",
                      }}
                    >
                      {t("common.openDashboard")}
                    </Link>
                    <Link
                      href={`/candidates?highlight=${candidateId}`}
                      className="btn btn--ghost btn--sm"
                      style={{ color: "var(--brand-paper)" }}
                    >
                      {t("common.goToCandidates")}
                    </Link>
                  </div>
                )}
              </div>
            )}

            {tab === "form" && (
              <>
                <FormSection title={t("upload.section.personal")} required>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput label={t("upload.field.lastName")} value={form.last_name} onChange={(value) => updateField("last_name", value)} placeholder="Akhmetzhanov" />
                    <FormInput label={t("upload.field.firstName")} value={form.first_name} onChange={(value) => updateField("first_name", value)} placeholder="Daniyar" />
                    <FormInput label={t("upload.field.patronymic")} value={form.patronymic} onChange={(value) => updateField("patronymic", value)} placeholder="Bakhytzhanovich" />
                    <FormInput label={t("upload.field.birthDate")} type="date" value={form.date_of_birth} onChange={(value) => updateField("date_of_birth", value)} />
                    <FormSelect
                      label={t("upload.field.gender")}
                      value={form.gender}
                      onChange={(value) => updateField("gender", value)}
                      options={[
                        { value: "", label: t("upload.field.gender.unspecified") },
                        { value: "male", label: t("upload.field.gender.male") },
                        { value: "female", label: t("upload.field.gender.female") },
                      ]}
                    />
                    <FormInput label={t("upload.field.citizenship")} value={form.citizenship} onChange={(value) => updateField("citizenship", value)} placeholder="KZ" />
                    <FormInput label={t("upload.field.email")} type="email" value={form.email} onChange={(value) => updateField("email", value)} placeholder="applicant@example.com" />
                    <FormInput label={t("upload.field.phone")} value={form.phone} onChange={(value) => updateField("phone", value)} placeholder="+7..." />
                  </div>
                </FormSection>

                <FormSection title={t("upload.section.academic")}>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormSelect
                      label={t("upload.field.program")}
                      value={form.selected_program}
                      onChange={(value) => updateField("selected_program", value)}
                      options={programOptions}
                    />
                    <FormSelect
                      label={t("upload.field.exam")}
                      value={form.language_exam_type}
                      onChange={(value) => updateField("language_exam_type", value)}
                      options={EXAM_TYPES.map((exam) => ({
                        value: exam,
                        label: exam || t("upload.field.exam.none"),
                      }))}
                    />
                    {form.language_exam_type && (
                      <FormInput
                        label={t("upload.field.score")}
                        type="number"
                        value={form.language_score}
                        onChange={(value) => updateField("language_score", value)}
                        placeholder="0.0 - 9.0"
                      />
                    )}
                  </div>
                </FormSection>

                <FormSection title={t("upload.section.content")}>
                  <div className="flex flex-col gap-4">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-[0.82rem] font-[700] text-muted-strong">
                          {t("upload.field.essay")} <span className="text-muted">({t("common.optional")})</span>
                        </label>
                        <span className="text-[0.76rem] font-[600] text-muted">
                          {wordCount(form.essay_text)} {t("upload.field.words")}
                        </span>
                      </div>
                      <textarea
                        value={form.essay_text}
                        onChange={(event) => updateField("essay_text", event.target.value)}
                        placeholder={t("upload.essayPlaceholder")}
                        rows={8}
                        className="px-4 py-3 text-[0.88rem] font-[500] resize-y"
                        style={{ lineHeight: 1.7 }}
                      />
                    </div>

                    <FormInput
                      label={t("upload.field.video")}
                      type="url"
                      value={form.video_url}
                      onChange={(value) => updateField("video_url", value)}
                      placeholder="https://..."
                    />

                    <FormInput
                      label={t("upload.field.telegram")}
                      value={form.telegram}
                      onChange={(value) => updateField("telegram", value)}
                      placeholder="@username"
                    />
                  </div>
                </FormSection>

                <CollapsibleSection title={t("upload.section.additional")}>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="sm:col-span-2 flex items-center gap-3">
                      <label className="flex items-center gap-2 cursor-pointer text-[0.84rem] font-[600]">
                        <input
                          type="checkbox"
                          checked={form.has_social_benefit}
                          onChange={(event) => updateField("has_social_benefit", event.target.checked)}
                          className="accent-[var(--brand-blue)] w-4 h-4"
                        />
                        {t("upload.field.socialStatus")}
                      </label>
                      {form.has_social_benefit && (
                        <input
                          type="text"
                          value={form.benefit_type}
                          onChange={(event) => updateField("benefit_type", event.target.value)}
                          placeholder={t("upload.field.benefitType")}
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
                    {showPreview ? t("common.hideJson") : t("common.showJson")}
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
                    {t("upload.submit")}
                  </button>
                </div>
              </>
            )}

            {tab === "json" && (
              <div className="card p-6 mb-6">
                <div className="eyebrow mb-4">{t("upload.json.title")}</div>
                <textarea
                  value={jsonInput}
                  onChange={(event) => {
                    setJsonInput(event.target.value);
                    handleReset();
                  }}
                  placeholder={t("upload.json.placeholder")}
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
                    {t("common.submit")}
                  </button>
                </div>
              </div>
            )}

            {tab === "demo" && (
              <section className="card p-6 lg:p-7">
                <div className="flex flex-col gap-2 mb-6">
                  <div className="eyebrow">{t("nav.demo")}</div>
                  <p className="text-[0.98rem] text-muted max-w-[70ch]">
                    {t("upload.demo.description")}
                  </p>
                </div>

                {fixturesLoading ? (
                  <div className="text-muted font-[700]">{t("common.loading")}</div>
                ) : fixtures.length === 0 ? (
                  <div className="text-muted font-[700]">{t("upload.demo.empty")}</div>
                ) : (
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                    {fixtures.map((fixture) => (
                      <DemoCard
                        key={fixture.meta.slug}
                        meta={fixture.meta}
                        onRun={handleRunFixture}
                        isRunning={runningDemoSlug === fixture.meta.slug}
                        isDisabled={Boolean(runningDemoSlug && runningDemoSlug !== fixture.meta.slug)}
                        actionLabel={t("upload.demo.run")}
                      />
                    ))}
                  </div>
                )}
              </section>
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
  const { t } = useLocale();

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
            {t("common.required")}
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
          <option key={`${option.value}-${option.label}`} value={option.value}>
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
