"use client";

import { useState } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";

export default function UploadPage() {
  const [jsonInput, setJsonInput] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit() {
    if (!jsonInput.trim()) return;

    setStatus("submitting");
    try {
      const parsed = JSON.parse(jsonInput);
      // TODO: connect to POST /api/v1/pipeline/submit
      setStatus("success");
      setMessage(`Кандидат успешно отправлен. Пайплайн обработки запущен.`);
      setJsonInput("");
    } catch {
      setStatus("error");
      setMessage("Неверный формат JSON. Проверьте введённые данные.");
    }
  }

  async function handleBatchSubmit() {
    if (!jsonInput.trim()) return;

    setStatus("submitting");
    try {
      const parsed = JSON.parse(jsonInput);
      if (!Array.isArray(parsed)) {
        throw new Error("Пакетная отправка ожидает JSON-массив");
      }
      // TODO: connect to POST /api/v1/pipeline/batch
      setStatus("success");
      setMessage(`${parsed.length} кандидатов отправлено на пакетную обработку.`);
      setJsonInput("");
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Неверный формат JSON.");
    }
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
            <p className="text-[0.95rem] mb-8" style={{ color: "var(--brand-muted)" }}>
              Отправьте данные кандидата в формате JSON для запуска пайплайна оценки ИИ
            </p>

            <div className="card p-6 mb-6">
              <div className="eyebrow mb-4">JSON-данные кандидата</div>
              <textarea
                value={jsonInput}
                onChange={(e) => {
                  setJsonInput(e.target.value);
                  setStatus("idle");
                }}
                placeholder={`{
  "personal": { "last_name": "...", "first_name": "...", ... },
  "academic": { "selected_program": "...", ... },
  "content": { "essay_text": "...", "video_url": "...", ... },
  "internal_test": { "answers": [...] }
}`}
                rows={16}
                className="w-full px-4 py-3 rounded-[1rem] text-[0.88rem] font-[500] outline-none resize-y font-mono"
                style={{
                  border: "1px solid rgba(20, 20, 20, 0.1)",
                  background: "rgba(255, 255, 255, 0.82)",
                  lineHeight: 1.6,
                }}
              />

              {status !== "idle" && (
                <div
                  className="mt-4 rounded-[var(--radius-md)] px-4 py-3 text-[0.88rem] font-[600]"
                  style={{
                    background:
                      status === "success"
                        ? "rgba(193, 241, 29, 0.18)"
                        : status === "error"
                          ? "rgba(255, 142, 112, 0.14)"
                          : "rgba(61, 237, 241, 0.12)",
                    color:
                      status === "success"
                        ? "#415005"
                        : status === "error"
                          ? "#ac472e"
                          : "#0a6a6d",
                  }}
                >
                  {status === "submitting" ? "Обработка..." : message}
                </div>
              )}

              <div className="flex gap-3 mt-5">
                <button
                  onClick={handleSubmit}
                  disabled={!jsonInput.trim() || status === "submitting"}
                  className="btn btn--dark"
                  style={{
                    opacity: !jsonInput.trim() || status === "submitting" ? 0.4 : 1,
                    cursor: !jsonInput.trim() || status === "submitting" ? "not-allowed" : "pointer",
                  }}
                >
                  Отправить
                </button>
                <button
                  onClick={handleBatchSubmit}
                  disabled={!jsonInput.trim() || status === "submitting"}
                  className="btn"
                  style={{
                    opacity: !jsonInput.trim() || status === "submitting" ? 0.4 : 1,
                    cursor: !jsonInput.trim() || status === "submitting" ? "not-allowed" : "pointer",
                  }}
                >
                  Пакетная отправка
                </button>
              </div>
            </div>

            <div className="card card--dark p-6">
              <div className="text-[0.76rem] font-[800] uppercase tracking-[0.12em] mb-3 opacity-60">
                Этапы пайплайна
              </div>
              <div className="flex flex-wrap gap-2 items-center text-[0.82rem] font-[700]">
                {[
                  "M2 Intake",
                  "M3 Privacy",
                  "M4 Profile",
                  "M13 ASR",
                  "M5 NLP",
                  "M6 Scoring",
                  "M7 Explain",
                ].map((step, i) => (
                  <span key={step} className="flex items-center gap-2">
                    <span
                      className="px-3 py-1.5 rounded-full text-[0.78rem]"
                      style={{
                        background: "rgba(193, 241, 29, 0.18)",
                        color: "#c1f11d",
                      }}
                    >
                      {step}
                    </span>
                    {i < 6 && <span style={{ color: "rgba(255,255,255,0.3)" }}>&rarr;</span>}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
