import type { SeriesPoint } from "@/lib/types";

/** Ability is clamped to this range by the model, so the axis is fixed. */
const MIN = -2;
const MAX = 2;

const WIDTH = 260;
const HEIGHT = 72;
const PAD = 6;

interface AbilitySparklineProps {
  series: SeriesPoint[];
  label: string;
}

function y(theta: number): number {
  const clamped = Math.min(MAX, Math.max(MIN, theta));
  const ratio = (clamped - MIN) / (MAX - MIN);
  return HEIGHT - PAD - ratio * (HEIGHT - PAD * 2);
}

function x(index: number, count: number): number {
  if (count <= 1) return WIDTH / 2;
  return PAD + (index / (count - 1)) * (WIDTH - PAD * 2);
}

/**
 * Ability over time for one topic.
 *
 * A fixed axis rather than one scaled to the data, so the three topic
 * cards can be compared at a glance — a line that rises steeply on one
 * card must mean the same thing as on the next.
 *
 * Correct and incorrect answers differ by fill as well as colour: filled
 * for correct, hollow for incorrect. design.md forbids colour carrying
 * meaning alone.
 */
export function AbilitySparkline({ series, label }: AbilitySparklineProps) {
  if (series.length === 0) {
    return (
      <div
        className="border-line text-ink-faint text-label flex items-center justify-center rounded-md border border-dashed"
        style={{ height: HEIGHT }}
      >
        No answers yet
      </div>
    );
  }

  const points = series.map((point, i) => ({
    cx: x(i, series.length),
    cy: y(point.theta),
    isCorrect: point.isCorrect,
  }));
  const path = points.map((p) => `${p.cx},${p.cy}`).join(" ");

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="h-[72px] w-full"
      role="img"
      aria-label={label}
    >
      {[MIN, 0, MAX].map((tick) => (
        <line
          key={tick}
          x1={0}
          x2={WIDTH}
          y1={y(tick)}
          y2={y(tick)}
          className="stroke-line"
          strokeWidth={tick === 0 ? 1.5 : 1}
          strokeDasharray={tick === 0 ? undefined : "3 3"}
        />
      ))}

      <polyline
        points={path}
        fill="none"
        className="stroke-accent"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {points.map((p, i) => (
        <circle
          key={i}
          cx={p.cx}
          cy={p.cy}
          r={3}
          strokeWidth={1.5}
          className={
            p.isCorrect
              ? "fill-correct stroke-correct"
              : "fill-surface stroke-incorrect"
          }
        />
      ))}
    </svg>
  );
}
