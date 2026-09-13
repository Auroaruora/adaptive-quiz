import type { ReactNode } from "react";

interface PanelProps {
  children: ReactNode;
  /**
   * `deep` is the one dark panel a screen is allowed — the thing the eye
   * should land on first. Never two on one screen.
   */
  tone?: "surface" | "deep";
  className?: string;
}

const TONE = {
  surface: "bg-surface border-line border shadow-raised",
  deep: "bg-deep text-surface",
} as const;

export function Panel({
  children,
  tone = "surface",
  className = "",
}: PanelProps) {
  return (
    <section className={`rounded-xl p-8 ${TONE[tone]} ${className}`}>
      {children}
    </section>
  );
}
