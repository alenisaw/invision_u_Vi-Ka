import type { EvidenceItem } from "@/types";
import { localizeLabel } from "@/lib/utils";

interface EvidenceListProps {
  evidence: EvidenceItem[];
}

export default function EvidenceList({ evidence }: EvidenceListProps) {
  return (
    <div className="flex flex-col gap-2">
      {evidence.map((item, i) => (
        <div
          key={i}
          className="flex gap-3 pl-3 border-l-2"
          style={{ borderColor: "var(--brand-lime)" }}
        >
          <div className="flex-1">
            <p className="text-[0.82rem] italic text-muted-strong">
              &ldquo;{item.quote}&rdquo;
            </p>
            <span
              className="text-[0.72rem] font-[700] mt-1 inline-block px-2 py-0.5 rounded-full text-muted-strong"
              style={{ background: "var(--surface-subtle-2)" }}
            >
              {item.source
                .split(",")
                .map((part) => localizeLabel(part.trim()))
                .join(", ")}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
