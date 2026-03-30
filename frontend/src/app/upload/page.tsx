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
  "Р В Р’В¦Р В РЎвЂР РЋРІР‚С›Р РЋР вЂљР В РЎвЂўР В Р вЂ Р РЋРІР‚в„–Р В Р’Вµ Р В РЎВР В Р’ВµР В РўвЂР В РЎвЂР В Р’В° Р В РЎвЂ Р В РЎВР В Р’В°Р РЋР вЂљР В РЎвЂќР В Р’ВµР РЋРІР‚С™Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“",
  "Р В Р’ВР В Р вЂ¦Р В Р вЂ¦Р В РЎвЂўР В Р вЂ Р В Р’В°Р РЋРІР‚В Р В РЎвЂР В РЎвЂўР В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р РЋРІР‚В Р В РЎвЂР РЋРІР‚С›Р РЋР вЂљР В РЎвЂўР В Р вЂ Р РЋРІР‚в„–Р В Р’Вµ Р В РЎвЂ”Р РЋР вЂљР В РЎвЂўР В РўвЂР РЋРЎвЂњР В РЎвЂќР РЋРІР‚С™Р РЋРІР‚в„– Р В РЎвЂ Р РЋР С“Р В Р’ВµР РЋР вЂљР В Р вЂ Р В РЎвЂР РЋР С“Р РЋРІР‚в„–",
  "Р В РЎв„ўР РЋР вЂљР В Р’ВµР В Р’В°Р РЋРІР‚С™Р В РЎвЂР В Р вЂ Р В Р вЂ¦Р В Р’В°Р РЋР РЏ Р В РЎвЂР В Р вЂ¦Р В Р’В¶Р В Р’ВµР В Р вЂ¦Р В Р’ВµР РЋР вЂљР В РЎвЂР РЋР РЏ",
  "Р В Р Р‹Р В РЎвЂўР РЋРІР‚В Р В РЎвЂР В РЎвЂўР В Р’В»Р В РЎвЂўР В РЎвЂ“Р В РЎвЂР РЋР РЏ Р В РЎвЂР В Р вЂ¦Р В Р вЂ¦Р В РЎвЂўР В Р вЂ Р В Р’В°Р РЋРІР‚В Р В РЎвЂР В РІвЂћвЂ“ Р В РЎвЂ Р В Р’В»Р В РЎвЂР В РўвЂР В Р’ВµР РЋР вЂљР РЋР С“Р РЋРІР‚С™Р В Р вЂ Р В Р’В°",
  "Р В Р Р‹Р РЋРІР‚С™Р РЋР вЂљР В Р’В°Р РЋРІР‚С™Р В Р’ВµР В РЎвЂ“Р В РЎвЂР В РЎвЂ Р В РЎвЂ“Р В РЎвЂўР РЋР С“Р РЋРЎвЂњР В РўвЂР В Р’В°Р РЋР вЂљР РЋР С“Р РЋРІР‚С™Р В Р вЂ Р В Р’ВµР В Р вЂ¦Р В Р вЂ¦Р В РЎвЂўР В РЎвЂ“Р В РЎвЂў Р РЋРЎвЂњР В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР РЋР РЏ Р В РЎвЂ Р РЋР вЂљР В Р’В°Р В Р’В·Р В Р вЂ Р В РЎвЂР РЋРІР‚С™Р В РЎвЂР РЋР РЏ",
  "General Admissions",
];

const EXAM_TYPES = ["IELTS", "TOEFL", "Kaztest", ""];

interface TestAnswer {
  question_id: string;
  answer: string;
}

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
  answers: TestAnswer[];
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
  answers: [{ question_id: "q1", answer: "" }],
  phone: "",
  telegram: "",
  has_social_benefit: false,
  benefit_type: "",
};

const PIPELINE_STEP_COUNT = 7;
const STATUS_POLL_INTERVAL_MS = 1800;
const MEDIA_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi", ".webm", ".wav", ".mp3", ".m4a", ".ogg", ".flac", ".mpeg", ".mpga"];
const TRUSTED_VIDEO_PAGE_HOST_SUFFIXES = [
  "youtube.com",
  "youtu.be",
  "vimeo.com",
  "drive.google.com",
  "docs.google.com",
  "dropbox.com",
  "dropboxusercontent.com",
];
const PIPELINE_STAGE_TO_STEP: Record<string, number> = {
  queued: 0,
  intake: 1,
  privacy: 2,
  asr: 3,
  profile: 4,
  nlp: 5,
  scoring: 6,
  explainability: 7,
  completed: PIPELINE_STEP_COUNT,
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
    internal_test: {
      answers: form.answers.filter((a) => a.answer.trim()),
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

function isDirectMediaUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return MEDIA_EXTENSIONS.some((extension) => parsed.pathname.toLowerCase().endsWith(extension));
  } catch {
    return false;
  }
}

function isTrustedVideoPageHost(hostname: string): boolean {
  return TRUSTED_VIDEO_PAGE_HOST_SUFFIXES.some(
    (suffix) => hostname === suffix || hostname.endsWith(`.${suffix}`),
  );
}

function isSafeVideoUrlCandidate(url: string): boolean {
  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.trim().toLowerCase();
    if (!["http:", "https:"].includes(parsed.protocol)) return false;
    if (!hostname || ["localhost", "127.0.0.1", "::1"].includes(hostname)) return false;
    if (parsed.username || parsed.password) return false;
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(hostname)) {
      if (
        hostname.startsWith("10.") ||
        hostname.startsWith("127.") ||
        hostname.startsWith("192.168.") ||
        /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)
      ) {
        return false;
      }
    }
    return isDirectMediaUrl(url) || isTrustedVideoPageHost(hostname);
  } catch {
    return false;
  }
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

  function resolvePipelineStep(pipelineStatus: string, currentStage?: string | null): number {
    if (pipelineStatus === "completed") {
      return PIPELINE_STEP_COUNT;
    }
    return Math.min(
      PIPELINE_STEP_COUNT,
      PIPELINE_STAGE_TO_STEP[currentStage ?? pipelineStatus] ?? 0,
    );
  }

  async function waitForPipelineCompletion(nextCandidateId: string) {
    const startedAt = Date.now();

    while (Date.now() - startedAt < 180000) {
      const snapshot = await pipelineApi.getCandidateStatus(nextCandidateId);
      setPipelineStep(
        resolvePipelineStep(snapshot.pipeline_status, snapshot.latest_job?.current_stage),
      );

      if (snapshot.pipeline_status === "completed") {
        return snapshot;
      }
      if (snapshot.pipeline_status === "failed") {
        throw new Error("Pipeline processing failed.");
      }
      if (snapshot.pipeline_status === "requires_manual_review") {
        throw new Error("Candidate was routed to manual review.");
      }

      await new Promise((resolve) => setTimeout(resolve, STATUS_POLL_INTERVAL_MS));
    }

    throw new Error("Timed out while waiting for pipeline completion.");
  }

  async function runPipeline(payload: unknown) {
    setStatus("running");
    setPipelineStep(0);
    setCandidateId("");
    setMessage("");

    try {
      const result = await pipelineApi.submitCandidate(payload);
      setCandidateId(result.candidate_id);
      setMessage("Candidate accepted. Pipeline job has been queued.");
      const snapshot = await waitForPipelineCompletion(result.candidate_id);
      setPipelineStep(PIPELINE_STEP_COUNT);
      setStatus("completed");
      setMessage(`Pipeline completed with status: ${snapshot.pipeline_status}`);
      setTimeout(() => router.push(`/dashboard/${result.candidate_id}`), 1500);
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Pipeline processing failed.");
    }
  }

  function handleFormSubmit() {
    if (!isFormValid) return;
    if (form.video_url.trim() && !isSafeVideoUrlCandidate(form.video_url.trim())) {
      setStatus("error");
      setMessage("Video URL must point to a direct media file or an approved public video host.");
      return;
    }
    runPipeline(buildPayload(form));
  }

  function handleJsonSubmit() {
    if (!jsonInput.trim()) return;
    try {
      runPipeline(JSON.parse(jsonInput));
    } catch {
      setStatus("error");
      setMessage("Invalid JSON payload.");
    }
  }

  async function handleBatchSubmit() {
    if (!jsonInput.trim()) return;
    setStatus("running");
    setPipelineStep(0);
    try {
      const parsed = JSON.parse(jsonInput);
      if (!Array.isArray(parsed)) throw new Error("Batch submission expects a JSON array.");
      const result = await pipelineApi.submitBatch(parsed);
      setStatus("completed");
      setPipelineStep(1);
      setMessage(`${result.length} candidate jobs queued for background processing.`);
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Batch submission failed.");
    }
  }

  function handleReset() {
    setStatus("idle");
    setMessage("");
    setCandidateId("");
    setPipelineStep(0);
  }

  // -- Helpers for dynamic lists --

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

  function addAnswer() {
    updateField("answers", [
      ...form.answers,
      { question_id: `q${form.answers.length + 1}`, answer: "" },
    ]);
  }

  function removeAnswer(idx: number) {
    updateField(
      "answers",
      form.answers.filter((_, i) => i !== idx),
    );
  }

  function updateAnswer(idx: number, field: "question_id" | "answer", value: string) {
    updateField(
      "answers",
      form.answers.map((a, i) => (i === idx ? { ...a, [field]: value } : a)),
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
              Р В РІР‚вЂќР В Р’В°Р В РЎвЂ“Р РЋР вЂљР РЋРЎвЂњР В Р’В·Р В РЎвЂќР В Р’В° Р В РЎвЂќР В Р’В°Р В Р вЂ¦Р В РўвЂР В РЎвЂР В РўвЂР В Р’В°Р РЋРІР‚С™Р В Р’В°
            </h1>
            <p className="text-[0.95rem] mb-6" style={{ color: "var(--brand-muted)" }}>
              Р В РІР‚вЂќР В Р’В°Р В РЎвЂ”Р В РЎвЂўР В Р’В»Р В Р вЂ¦Р В РЎвЂР РЋРІР‚С™Р В Р’Вµ Р В Р’В°Р В Р вЂ¦Р В РЎвЂќР В Р’ВµР РЋРІР‚С™Р РЋРЎвЂњ Р В РЎвЂР В Р’В»Р В РЎвЂ Р В Р’В·Р В Р’В°Р В РЎвЂ“Р РЋР вЂљР РЋРЎвЂњР В Р’В·Р В РЎвЂР РЋРІР‚С™Р В Р’Вµ JSON Р В РўвЂР В Р’В»Р РЋР РЏ Р В Р’В·Р В Р’В°Р В РЎвЂ”Р РЋРЎвЂњР РЋР С“Р В РЎвЂќР В Р’В° Р В РЎвЂ”Р В Р’В°Р В РІвЂћвЂ“Р В РЎвЂ”Р В Р’В»Р В Р’В°Р В РІвЂћвЂ“Р В Р вЂ¦Р В Р’В° Р В РЎвЂўР РЋРІР‚В Р В Р’ВµР В Р вЂ¦Р В РЎвЂќР В РЎвЂ
            </p>

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
              {(["form", "json"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => { setTab(t); handleReset(); }}
                  className="chip"
                  style={{
                    background: tab === t ? "var(--brand-ink)" : "rgba(20, 20, 20, 0.05)",
                    color: tab === t ? "#fff" : "var(--brand-muted-strong)",
                  }}
                >
                  {t === "form" ? "Р В РЎвЂ™Р В Р вЂ¦Р В РЎвЂќР В Р’ВµР РЋРІР‚С™Р В Р’В°" : "JSON"}
                </button>
              ))}
            </div>

            {/* Pipeline progress */}
            {status !== "idle" && (
              <div className="card card--dark p-5 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-[0.82rem] font-[700]" style={{ color: "#fff" }}>
                    {status === "running"
                      ? "Р В РЎвЂєР В Р’В±Р РЋР вЂљР В Р’В°Р В Р’В±Р В РЎвЂўР РЋРІР‚С™Р В РЎвЂќР В Р’В° Р В РЎвЂќР В Р’В°Р В Р вЂ¦Р В РўвЂР В РЎвЂР В РўвЂР В Р’В°Р РЋРІР‚С™Р В Р’В°..."
                      : status === "completed"
                        ? "Р В РІР‚СљР В РЎвЂўР РЋРІР‚С™Р В РЎвЂўР В Р вЂ Р В РЎвЂў! Р В РЎСџР В Р’ВµР РЋР вЂљР В Р’ВµР РЋРІР‚В¦Р В РЎвЂўР В РўвЂ Р В РЎвЂќ Р РЋР вЂљР В Р’ВµР В Р’В·Р РЋРЎвЂњР В Р’В»Р РЋР Р‰Р РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р В Р’В°Р В РЎВ..."
                        : `Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В°: ${message}`}
                  </div>
                  {(status === "error" || status === "completed") && (
                    <button
                      onClick={handleReset}
                      className="text-[0.78rem] font-[600]"
                      style={{ color: "rgba(255,255,255,0.6)" }}
                    >
                      Р В РІР‚вЂќР В Р’В°Р В РЎвЂќР РЋР вЂљР РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰
                    </button>
                  )}
                </div>
                <PipelineProgress status={status} currentStep={pipelineStep} />
                {status === "completed" && candidateId && (
                  <div className="flex gap-3 mt-4">
                    <Link href={`/dashboard/${candidateId}`} className="btn btn--sm" style={{ background: "var(--brand-lime)", color: "#000" }}>
                      Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂќР РЋР вЂљР РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂќР В Р’В°Р РЋР вЂљР РЋРІР‚С™Р В РЎвЂўР РЋРІР‚РЋР В РЎвЂќР РЋРЎвЂњ
                    </Link>
                    <Link href="/dashboard" className="btn btn--ghost btn--sm" style={{ color: "rgba(255,255,255,0.7)" }}>
                      Р В РЎСџР В Р’ВµР РЋР вЂљР В Р’ВµР В РІвЂћвЂ“Р РЋРІР‚С™Р В РЎвЂ Р В Р вЂ  Р РЋР вЂљР В Р’ВµР В РІвЂћвЂ“Р РЋРІР‚С™Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* === FORM TAB === */}
            {tab === "form" && (
              <>
                {/* Section 1: Personal */}
                <FormSection title="Р В РІР‚С”Р В РЎвЂР РЋРІР‚РЋР В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р В РўвЂР В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ" required>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput label="Р В Р’В¤Р В Р’В°Р В РЎВР В РЎвЂР В Р’В»Р В РЎвЂР РЋР РЏ *" value={form.last_name} onChange={(v) => updateField("last_name", v)} />
                    <FormInput label="Р В Р’ВР В РЎВР РЋР РЏ *" value={form.first_name} onChange={(v) => updateField("first_name", v)} />
                    <FormInput label="Р В РЎвЂєР РЋРІР‚С™Р РЋРІР‚РЋР В Р’ВµР РЋР С“Р РЋРІР‚С™Р В Р вЂ Р В РЎвЂў" value={form.patronymic} onChange={(v) => updateField("patronymic", v)} />
                    <FormInput label="Р В РІР‚СњР В Р’В°Р РЋРІР‚С™Р В Р’В° Р РЋР вЂљР В РЎвЂўР В Р’В¶Р В РўвЂР В Р’ВµР В Р вЂ¦Р В РЎвЂР РЋР РЏ *" type="date" value={form.date_of_birth} onChange={(v) => updateField("date_of_birth", v)} />
                    <FormSelect label="Р В РЎСџР В РЎвЂўР В Р’В»" value={form.gender} onChange={(v) => updateField("gender", v)} options={[
                      { value: "", label: "Р В РЎСљР В Р’Вµ Р РЋРЎвЂњР В РЎвЂќР В Р’В°Р В Р’В·Р В Р’В°Р В Р вЂ¦" },
                      { value: "male", label: "Р В РЎС™Р РЋРЎвЂњР В Р’В¶Р РЋР С“Р В РЎвЂќР В РЎвЂўР В РІвЂћвЂ“" },
                      { value: "female", label: "Р В РІР‚вЂњР В Р’ВµР В Р вЂ¦Р РЋР С“Р В РЎвЂќР В РЎвЂР В РІвЂћвЂ“" },
                    ]} />
                    <FormInput label="Р В РІР‚СљР РЋР вЂљР В Р’В°Р В Р’В¶Р В РўвЂР В Р’В°Р В Р вЂ¦Р РЋР С“Р РЋРІР‚С™Р В Р вЂ Р В РЎвЂў" value={form.citizenship} onChange={(v) => updateField("citizenship", v)} placeholder="KZ" />
                  </div>
                </FormSection>

                {/* Section 2: Academic */}
                <FormSection title="Р В РЎвЂєР В Р’В±Р РЋР вЂљР В Р’В°Р В Р’В·Р В РЎвЂўР В Р вЂ Р В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormSelect label="Р В РЎСџР РЋР вЂљР В РЎвЂўР В РЎвЂ“Р РЋР вЂљР В Р’В°Р В РЎВР В РЎВР В Р’В° *" value={form.selected_program} onChange={(v) => updateField("selected_program", v)} options={PROGRAMS.map((p) => ({ value: p, label: p }))} />
                    <FormSelect label="Р В Р вЂЎР В Р’В·Р РЋРІР‚в„–Р В РЎвЂќР В РЎвЂўР В Р вЂ Р В РЎвЂўР В РІвЂћвЂ“ Р РЋР РЉР В РЎвЂќР В Р’В·Р В Р’В°Р В РЎВР В Р’ВµР В Р вЂ¦" value={form.language_exam_type} onChange={(v) => updateField("language_exam_type", v)} options={EXAM_TYPES.map((t) => ({ value: t, label: t || "Р В РЎСљР В Р’Вµ Р РЋР С“Р В РўвЂР В Р’В°Р В Р вЂ Р В Р’В°Р В Р’В»" }))} />
                    {form.language_exam_type && (
                      <FormInput label="Р В РІР‚ВР В Р’В°Р В Р’В»Р В Р’В»" type="number" value={form.language_score} onChange={(v) => updateField("language_score", v)} placeholder="0.0 Р Р†Р вЂљРІР‚Сљ 9.0" />
                    )}
                  </div>
                </FormSection>

                {/* Section 3: Content */}
                <FormSection title="Р В РЎв„ўР В РЎвЂўР В Р вЂ¦Р РЋРІР‚С™Р В Р’ВµР В Р вЂ¦Р РЋРІР‚С™">
                  <div className="flex flex-col gap-4">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-[0.82rem] font-[700]" style={{ color: "var(--brand-muted-strong)" }}>Р В Р’В­Р РЋР С“Р РЋР С“Р В Р’Вµ</label>
                        <span className="text-[0.76rem] font-[600]" style={{ color: "var(--brand-muted)" }}>
                          {wordCount(form.essay_text)} Р РЋР С“Р В Р’В»Р В РЎвЂўР В Р вЂ 
                        </span>
                      </div>
                      <textarea
                        value={form.essay_text}
                        onChange={(e) => updateField("essay_text", e.target.value)}
                        placeholder="Р В РЎСљР В Р’В°Р В РЎвЂ”Р В РЎвЂР РЋРІвЂљВ¬Р В РЎвЂР РЋРІР‚С™Р В Р’Вµ Р В РЎВР В РЎвЂўР РЋРІР‚С™Р В РЎвЂР В Р вЂ Р В Р’В°Р РЋРІР‚В Р В РЎвЂР В РЎвЂўР В Р вЂ¦Р В Р вЂ¦Р В РЎвЂўР В Р’Вµ Р РЋР РЉР РЋР С“Р РЋР С“Р В Р’Вµ (3Р Р†Р вЂљРІР‚Сљ5 Р В Р’В°Р В Р’В±Р В Р’В·Р В Р’В°Р РЋРІР‚В Р В Р’ВµР В Р вЂ )..."
                        rows={8}
                        className="w-full px-4 py-3 rounded-[1rem] text-[0.88rem] font-[500] outline-none resize-y"
                        style={{ border: "1px solid rgba(20, 20, 20, 0.1)", background: "rgba(255, 255, 255, 0.82)", lineHeight: 1.7 }}
                      />
                    </div>
                    <FormInput label="Р В Р Р‹Р РЋР С“Р РЋРІР‚в„–Р В Р’В»Р В РЎвЂќР В Р’В° Р В Р вЂ¦Р В Р’В° Р В Р вЂ Р В РЎвЂР В РўвЂР В Р’ВµР В РЎвЂў-Р В РЎвЂР В Р вЂ¦Р РЋРІР‚С™Р В Р’ВµР РЋР вЂљР В Р вЂ Р РЋР Р‰Р РЋР вЂ№" value={form.video_url} onChange={(v) => updateField("video_url", v)} placeholder="https://..." />
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-[0.82rem] font-[700]" style={{ color: "var(--brand-muted-strong)" }}>Р В РЎСџР РЋР вЂљР В РЎвЂўР В Р’ВµР В РЎвЂќР РЋРІР‚С™Р РЋРІР‚в„–</label>
                        <button onClick={addProject} className="text-[0.78rem] font-[700]" style={{ color: "var(--brand-blue)" }}>+ Р В РІР‚СњР В РЎвЂўР В Р’В±Р В Р’В°Р В Р вЂ Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰</button>
                      </div>
                      <div className="flex flex-col gap-2">
                        {form.project_descriptions.map((p, i) => (
                          <div key={i} className="flex gap-2">
                            <input
                              value={p}
                              onChange={(e) => updateProject(i, e.target.value)}
                              placeholder={`Р В РЎСџР РЋР вЂљР В РЎвЂўР В Р’ВµР В РЎвЂќР РЋРІР‚С™ ${i + 1}: Р В РЎвЂўР В РЎвЂ”Р В РЎвЂР РЋР С“Р В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ...`}
                              className="flex-1 px-4 py-2.5 rounded-[1rem] text-[0.86rem] font-[500] outline-none"
                              style={{ border: "1px solid rgba(20, 20, 20, 0.1)", background: "rgba(255, 255, 255, 0.82)" }}
                            />
                            {form.project_descriptions.length > 1 && (
                              <button onClick={() => removeProject(i)} className="text-[0.82rem] font-[600] px-2" style={{ color: "var(--brand-coral)" }}>Р вЂњРІР‚вЂќ</button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                    <FormInput label="Р В РЎв„ўР РЋР вЂљР В Р’В°Р РЋРІР‚С™Р В РЎвЂќР В РЎвЂўР В Р’Вµ Р В РЎвЂўР В РЎвЂ”Р В РЎвЂР РЋР С“Р В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В РЎвЂўР В РЎвЂ”Р РЋРІР‚в„–Р РЋРІР‚С™Р В Р’В°" value={form.experience_summary} onChange={(v) => updateField("experience_summary", v)} placeholder="Р В РЎвЂєР В РЎвЂ”Р РЋРІР‚в„–Р РЋРІР‚С™, Р В Р вЂ¦Р В Р’В°Р В Р вЂ Р РЋРІР‚в„–Р В РЎвЂќР В РЎвЂ, Р В РўвЂР В РЎвЂўР РЋР С“Р РЋРІР‚С™Р В РЎвЂР В Р’В¶Р В Р’ВµР В Р вЂ¦Р В РЎвЂР РЋР РЏ..." />
                  </div>
                </FormSection>

                {/* Section 4: Internal Test */}
                <FormSection title="Р В РІР‚в„ўР В Р вЂ¦Р РЋРЎвЂњР РЋРІР‚С™Р РЋР вЂљР В Р’ВµР В Р вЂ¦Р В Р вЂ¦Р В РЎвЂР В РІвЂћвЂ“ Р РЋРІР‚С™Р В Р’ВµР РЋР С“Р РЋРІР‚С™">
                  <div className="flex flex-col gap-3">
                    {form.answers.map((a, i) => (
                      <div key={i} className="card p-4" style={{ background: "rgba(20,20,20,0.02)" }}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[0.78rem] font-[700]" style={{ color: "var(--brand-muted)" }}>
                            Р В РІР‚в„ўР В РЎвЂўР В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋР С“ {a.question_id}
                          </span>
                          {form.answers.length > 1 && (
                            <button onClick={() => removeAnswer(i)} className="text-[0.78rem] font-[600]" style={{ color: "var(--brand-coral)" }}>Р В Р в‚¬Р В РўвЂР В Р’В°Р В Р’В»Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰</button>
                          )}
                        </div>
                        <textarea
                          value={a.answer}
                          onChange={(e) => updateAnswer(i, "answer", e.target.value)}
                          placeholder="Р В РІР‚в„ўР В Р’В°Р РЋРІвЂљВ¬ Р В РЎвЂўР РЋРІР‚С™Р В Р вЂ Р В Р’ВµР РЋРІР‚С™..."
                          rows={3}
                          className="w-full px-4 py-2.5 rounded-[1rem] text-[0.86rem] font-[500] outline-none resize-y"
                          style={{ border: "1px solid rgba(20, 20, 20, 0.1)", background: "rgba(255, 255, 255, 0.82)", lineHeight: 1.6 }}
                        />
                      </div>
                    ))}
                    <button onClick={addAnswer} className="text-[0.82rem] font-[700] self-start" style={{ color: "var(--brand-blue)" }}>
                      + Р В РІР‚СњР В РЎвЂўР В Р’В±Р В Р’В°Р В Р вЂ Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р В Р вЂ Р В РЎвЂўР В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋР С“
                    </button>
                  </div>
                </FormSection>

                {/* Section 5: Optional */}
                <CollapsibleSection title="Р В РІР‚СњР В РЎвЂўР В РЎвЂ”Р В РЎвЂўР В Р’В»Р В Р вЂ¦Р В РЎвЂР РЋРІР‚С™Р В Р’ВµР В Р’В»Р РЋР Р‰Р В Р вЂ¦Р В РЎвЂў (Р В Р вЂ¦Р В Р’ВµР В РЎвЂўР В Р’В±Р РЋР РЏР В Р’В·Р В Р’В°Р РЋРІР‚С™Р В Р’ВµР В Р’В»Р РЋР Р‰Р В Р вЂ¦Р В РЎвЂў)">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput label="Р В РЎС›Р В Р’ВµР В Р’В»Р В Р’ВµР РЋРІР‚С›Р В РЎвЂўР В Р вЂ¦" value={form.phone} onChange={(v) => updateField("phone", v)} placeholder="+7..." />
                    <FormInput label="Telegram" value={form.telegram} onChange={(v) => updateField("telegram", v)} placeholder="@username" />
                    <div className="sm:col-span-2 flex items-center gap-3">
                      <label className="flex items-center gap-2 cursor-pointer text-[0.84rem] font-[600]">
                        <input
                          type="checkbox"
                          checked={form.has_social_benefit}
                          onChange={(e) => updateField("has_social_benefit", e.target.checked)}
                          className="accent-[#3dedf1] w-4 h-4"
                        />
                        Р В Р Р‹Р В РЎвЂўР РЋРІР‚В Р В РЎвЂР В Р’В°Р В Р’В»Р РЋР Р‰Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ Р РЋР С“Р РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р РЋРЎвЂњР РЋР С“
                      </label>
                      {form.has_social_benefit && (
                        <input
                          value={form.benefit_type}
                          onChange={(e) => updateField("benefit_type", e.target.value)}
                          placeholder="Р В РЎС›Р В РЎвЂР В РЎвЂ” Р В Р’В»Р РЋР Р‰Р В РЎвЂ“Р В РЎвЂўР РЋРІР‚С™Р РЋРІР‚в„–..."
                          className="flex-1 px-3 py-2 rounded-[1rem] text-[0.84rem] font-[500] outline-none"
                          style={{ border: "1px solid rgba(20, 20, 20, 0.1)", background: "rgba(255, 255, 255, 0.82)" }}
                        />
                      )}
                    </div>
                  </div>
                </CollapsibleSection>

                {/* Preview JSON toggle */}
                <div className="mt-4 mb-2">
                  <button
                    onClick={() => setShowPreview(!showPreview)}
                    className="text-[0.82rem] font-[700]"
                    style={{ color: "var(--brand-muted)" }}
                  >
                    {showPreview ? "Р В Р Р‹Р В РЎвЂќР РЋР вЂљР РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ JSON" : "Р В РЎСџР В РЎвЂўР В РЎвЂќР В Р’В°Р В Р’В·Р В Р’В°Р РЋРІР‚С™Р РЋР Р‰ JSON"}
                  </button>
                  {showPreview && (
                    <pre
                      className="mt-2 px-4 py-3 rounded-[1rem] text-[0.78rem] font-mono overflow-x-auto max-h-[300px] overflow-y-auto"
                      style={{ background: "rgba(20, 20, 20, 0.04)", border: "1px solid rgba(20, 20, 20, 0.06)" }}
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
                    className="btn btn--dark"
                    style={{
                      opacity: !isFormValid || status === "running" ? 0.4 : 1,
                      cursor: !isFormValid || status === "running" ? "not-allowed" : "pointer",
                    }}
                  >
                    Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р В Р вЂ¦Р В Р’В° Р В РЎвЂўР РЋРІР‚В Р В Р’ВµР В Р вЂ¦Р В РЎвЂќР РЋРЎвЂњ
                  </button>
                </div>
              </>
            )}

            {/* === JSON TAB === */}
            {tab === "json" && (
              <div className="card p-6 mb-6">
                <div className="eyebrow mb-4">JSON-Р В РўвЂР В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р В РЎвЂќР В Р’В°Р В Р вЂ¦Р В РўвЂР В РЎвЂР В РўвЂР В Р’В°Р РЋРІР‚С™Р В Р’В°</div>
                <textarea
                  value={jsonInput}
                  onChange={(e) => { setJsonInput(e.target.value); handleReset(); }}
                  placeholder={`{
  "personal": { "last_name": "...", "first_name": "...", "date_of_birth": "2007-01-01" },
  "academic": { "selected_program": "..." },
  "content": { "essay_text": "...", "video_url": "..." },
  "internal_test": { "answers": [...] }
}`}
                  rows={16}
                  data-testid="candidate-json-input"
                  className="w-full px-4 py-3 rounded-[1rem] text-[0.88rem] font-[500] outline-none resize-y font-mono"
                  style={{ border: "1px solid rgba(20, 20, 20, 0.1)", background: "rgba(255, 255, 255, 0.82)", lineHeight: 1.6 }}
                />
                <div className="flex gap-3 mt-5">
                  <button
                    onClick={handleJsonSubmit}
                    disabled={!jsonInput.trim() || status === "running"}
                    data-testid="submit-json-button"
                    className="btn btn--dark"
                    style={{
                      opacity: !jsonInput.trim() || status === "running" ? 0.4 : 1,
                      cursor: !jsonInput.trim() || status === "running" ? "not-allowed" : "pointer",
                    }}
                  >
                    Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰
                  </button>
                  <button
                    onClick={handleBatchSubmit}
                    disabled={!jsonInput.trim() || status === "running"}
                    className="btn"
                    style={{
                      opacity: !jsonInput.trim() || status === "running" ? 0.4 : 1,
                      cursor: !jsonInput.trim() || status === "running" ? "not-allowed" : "pointer",
                    }}
                  >
                    Р В РЎСџР В Р’В°Р В РЎвЂќР В Р’ВµР РЋРІР‚С™Р В Р вЂ¦Р В Р’В°Р РЋР РЏ Р В РЎвЂўР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂќР В Р’В°
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
        {required && <span className="text-[0.7rem] font-[700] px-1.5 py-0.5 rounded-full" style={{ background: "rgba(255, 142, 112, 0.14)", color: "#ac472e" }}>Р В РЎвЂўР В Р’В±Р РЋР РЏР В Р’В·Р В Р’В°Р РЋРІР‚С™Р В Р’ВµР В Р’В»Р РЋР Р‰Р В Р вЂ¦Р В РЎвЂў</span>}
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
      <label className="block text-[0.82rem] font-[700] mb-1.5" style={{ color: "var(--brand-muted-strong)" }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 rounded-[1rem] text-[0.86rem] font-[500] outline-none"
        style={{ border: "1px solid rgba(20, 20, 20, 0.1)", background: "rgba(255, 255, 255, 0.82)" }}
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
      <label className="block text-[0.82rem] font-[700] mb-1.5" style={{ color: "var(--brand-muted-strong)" }}>
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2.5 rounded-[1rem] text-[0.86rem] font-[500] outline-none appearance-none"
        style={{ border: "1px solid rgba(20, 20, 20, 0.1)", background: "rgba(255, 255, 255, 0.82)" }}
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
        <span className="text-[0.82rem] font-[700]" style={{ color: "var(--brand-muted)" }}>
          {open ? "Р Р†РІвЂљВ¬РІР‚в„ў" : "+"}
        </span>
      </button>
      {open && <div className="mt-4">{children}</div>}
    </div>
  );
}
