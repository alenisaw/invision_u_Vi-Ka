import type { EvidenceItem } from "@/types";

interface EvidenceListProps {
  evidence: EvidenceItem[];
}

export default function EvidenceList({ evidence }: EvidenceListProps) {
  return (
    <div className="flex flex-col gap-2">
      {evidence.map((item, i) => (
        <div
          key={i}
          className="flex gap-3 pl-3"
          style={{ borderLeft: "2px solid var(--brand-lime)" }}
        >
          <div className="flex-1">
            <p className="text-[0.82rem] italic" style={{ color: "var(--brand-muted-strong)" }}>
              &ldquo;{item.quote}&rdquo;
            </p>
            <span
              className="text-[0.72rem] font-[700] mt-1 inline-block px-2 py-0.5 rounded-full"
              style={{
                background: "rgba(61, 237, 241, 0.12)",
                color: "#0a6a6d",
              }}
            >
              {item.source}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
