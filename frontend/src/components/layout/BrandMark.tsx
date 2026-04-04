"use client";

import { useState } from "react";
import { useLocale } from "@/components/providers/LocaleProvider";

interface BrandMarkProps {
  size?: "sm" | "lg";
}

export default function BrandMark({ size = "sm" }: BrandMarkProps) {
  const { t } = useLocale();
  const [clickCount, setClickCount] = useState(0);
  const isLarge = size === "lg";

  function handleClick() {
    const nextCount = clickCount + 1;
    if (nextCount >= 5) {
      setClickCount(0);
      window.open("https://youtu.be/dQw4w9WgXcQ", "_blank", "noopener,noreferrer");
      return;
    }
    setClickCount(nextCount);
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`group inline-flex items-center gap-3 rounded-full text-left transition-transform duration-200 hover:-translate-y-[1px] ${
        isLarge ? "px-1 py-1" : "px-1 py-1"
      }`}
      title={t("header.rickroll")}
      aria-label={t("header.rickroll")}
    >
      <span
        className={`shrink-0 rounded-full border border-white/10 shadow-[0_12px_32px_rgba(0,0,0,0.18)] ${
          isLarge ? "h-16 w-16" : "h-11 w-11"
        }`}
        style={{
          background:
            "radial-gradient(circle at 28% 24%, rgba(255,255,255,0.26) 0, transparent 28%), linear-gradient(135deg, var(--brand-lime) 0%, var(--brand-blue) 54%, var(--brand-coral) 100%)",
        }}
      />

      <span className="flex min-w-0 flex-col">
        <span
          className={`font-[900] leading-none tracking-[-0.08em] ${
            isLarge ? "text-[clamp(2.2rem,1.8rem+1.6vw,3.6rem)]" : "text-[1.65rem]"
          }`}
          style={{
            background:
              "linear-gradient(120deg, var(--brand-lime) 0%, var(--brand-blue) 48%, var(--brand-coral) 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            color: "transparent",
            textShadow: "0 14px 36px color-mix(in srgb, var(--brand-blue) 18%, transparent)",
          }}
        >
          invisionU
        </span>
        <span
          className={`font-[700] leading-none text-muted ${
            isLarge ? "mt-2 text-[0.9rem]" : "mt-1 text-[0.72rem]"
          }`}
        >
          {t("brand.committee")}
        </span>
      </span>
    </button>
  );
}
