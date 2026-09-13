interface AbilityDeltaProps {
  thetaBefore: number;
  thetaAfter: number;
}

/**
 * How far the answer moved the student's ability estimate.
 *
 * Shows the change rather than the raw value: a logit means nothing on its
 * own, but "went up a little" is readable. The arrow and the sign both
 * carry the direction, so colour is never doing the work alone.
 */
export function AbilityDelta({ thetaBefore, thetaAfter }: AbilityDeltaProps) {
  const delta = thetaAfter - thetaBefore;
  const rose = delta >= 0;
  const tone = rose ? "text-correct-ink" : "text-incorrect-ink";

  return (
    <p className="flex items-center gap-2">
      <span className="text-label text-ink-muted">Ability</span>
      <span className={`font-mono text-mono-xs ${tone}`}>
        <span aria-hidden="true">{rose ? "▲" : "▼"}</span> {rose ? "+" : "−"}
        {Math.abs(delta).toFixed(2)}
      </span>
      <span className="sr-only">
        {rose ? "increased" : "decreased"} by {Math.abs(delta).toFixed(2)}
      </span>
    </p>
  );
}
