"use client";

import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { MOCK_AUDIT_LOG, MOCK_CANDIDATES } from "@/lib/mock-data";
import { formatDateTime } from "@/lib/utils";

const ACTION_STYLES: Record<string, { bg: string; color: string }> = {
  shortlist_add: { bg: "rgba(193, 241, 29, 0.28)", color: "#415005" },
  override: { bg: "rgba(255, 142, 112, 0.18)", color: "#ac472e" },
  comment: { bg: "rgba(61, 237, 241, 0.18)", color: "#0a6a6d" },
  shortlist_remove: { bg: "rgba(20, 20, 20, 0.06)", color: "rgba(20, 20, 20, 0.76)" },
};

export default function AuditPage() {
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
              Журнал действий
            </h1>
            <p className="text-[0.95rem] mb-8" style={{ color: "var(--brand-muted)" }}>
              Все действия рецензентов и системные события зафиксированы для прозрачности
            </p>

            <div className="card overflow-hidden" style={{ borderRadius: "1rem" }}>
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(20, 20, 20, 0.07)" }}>
                    <th className="eyebrow px-5 py-4 text-left">Время</th>
                    <th className="eyebrow px-5 py-4 text-left">Рецензент</th>
                    <th className="eyebrow px-5 py-4 text-left">Кандидат</th>
                    <th className="eyebrow px-5 py-4 text-left">Действие</th>
                    <th className="eyebrow px-5 py-4 text-left">Смена статуса</th>
                    <th className="eyebrow px-5 py-4 text-left">Комментарий</th>
                  </tr>
                </thead>
                <tbody>
                  {MOCK_AUDIT_LOG.map((action) => {
                    const candidate = MOCK_CANDIDATES.find(
                      (c) => c.candidate_id === action.candidate_id
                    );
                    const style = ACTION_STYLES[action.action_type] ?? ACTION_STYLES.comment;

                    return (
                      <tr
                        key={action.id}
                        style={{ borderBottom: "1px solid rgba(20, 20, 20, 0.05)" }}
                      >
                        <td className="px-5 py-4">
                          <span className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>
                            {formatDateTime(action.created_at)}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-[0.88rem] font-[700]">{action.reviewer_id}</span>
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-[0.88rem] font-[800]">
                            {candidate?.name ?? action.candidate_id.slice(0, 8)}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <span
                            className="badge text-[0.72rem]"
                            style={{ background: style.bg, color: style.color }}
                          >
                            {action.action_type.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          {action.previous_status !== action.new_status ? (
                            <span className="text-[0.82rem]">
                              <span style={{ color: "var(--brand-muted)" }}>{action.previous_status}</span>
                              {" → "}
                              <span className="font-[700]">{action.new_status}</span>
                            </span>
                          ) : (
                            <span className="text-[0.82rem]" style={{ color: "var(--brand-muted)" }}>—</span>
                          )}
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-[0.82rem]" style={{ color: "var(--brand-muted-strong)" }}>
                            {action.comment}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
