import type { ReactNode } from "react";

interface RingProps {
  total: number;
  correct: number;
  wrong: number;
  /** Diameter in px. A layout dimension, which design.md leaves untokened. */
  size?: number;
  /** Drawn in the middle; only sensible at larger sizes. */
  children?: ReactNode;
  label: string;
}

/**
 * Where a set of questions stands, as one ring in three parts.
 *
 * Green for last answered right, orange for last answered wrong, and grey
 * for not yet practised, always in that order from the top, so position
 * distinguishes the parts as well as colour. The parts are counted in
 * questions and always add up to the whole; a ring never shows a share of
 * attempts, which would not.
 *
 * Nothing answered yet draws a plain grey ring rather than an empty one,
 * so an untouched topic still reads as "eighteen to go".
 */
export function Ring({
  total,
  correct,
  wrong,
  size = 32,
  children,
  label,
}: RingProps) {
  const stroke = Math.max(3, Math.round(size / 9));
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const share = (n: number) => (total === 0 ? 0 : (n / total) * circumference);

  const arcs = [
    { className: "stroke-correct", length: share(correct), offset: 0 },
    {
      className: "stroke-incorrect",
      length: share(wrong),
      offset: share(correct),
    },
  ];

  return (
    <div
      role="img"
      aria-label={label}
      className="relative inline-flex shrink-0 items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg
        viewBox={`0 0 ${size} ${size}`}
        className="h-full w-full -rotate-90"
        aria-hidden="true"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          className="stroke-line"
        />
        {arcs.map(
          (arc) =>
            arc.length > 0 && (
              <circle
                key={arc.className}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                strokeWidth={stroke}
                strokeDasharray={`${arc.length} ${circumference - arc.length}`}
                strokeDashoffset={-arc.offset}
                className={arc.className}
              />
            ),
        )}
      </svg>
      {children && (
        <div className="absolute inset-0 flex items-center justify-center">
          {children}
        </div>
      )}
    </div>
  );
}

/** The counts behind a ring, in words, so colour is never the only channel. */
export function RingLegend({
  total,
  correct,
  wrong,
}: {
  total: number;
  correct: number;
  wrong: number;
}) {
  const unseen = total - correct - wrong;
  const parts = [
    correct > 0 && (
      <span key="c" className="text-correct-ink">
        {correct} correct
      </span>
    ),
    wrong > 0 && (
      <span key="w" className="text-incorrect-ink">
        {wrong} wrong
      </span>
    ),
    unseen > 0 && (
      <span key="u" className="text-ink-faint">
        {unseen} to go
      </span>
    ),
  ].filter(Boolean);

  return (
    <span className="text-label">
      {parts.map((part, i) => (
        <span key={i}>
          {i > 0 && <span className="text-ink-faint"> · </span>}
          {part}
        </span>
      ))}
    </span>
  );
}

/** A sentence for screen readers and tooltips describing a ring. */
export function ringLabel(
  what: string,
  { total, correct, wrong }: { total: number; correct: number; wrong: number },
): string {
  const unseen = total - correct - wrong;
  return `${what}: ${correct} correct, ${wrong} wrong, ${unseen} not yet practised, of ${total}`;
}
