interface AbilityGainProps {
  thetaBefore: number;
  thetaAfter: number;
}

/**
 * Shows that the answer moved the ability estimate up. Shows nothing when
 * it moved down.
 *
 * A falling number after a wrong answer is discouraging and teaches
 * nothing the feedback does not already say better. The estimate still
 * falls — this only declines to narrate it, which is why the component is
 * named for a gain rather than a delta. It never reports a rise that did
 * not happen.
 */
export function AbilityGain({ thetaBefore, thetaAfter }: AbilityGainProps) {
  const gain = thetaAfter - thetaBefore;
  if (gain <= 0) return null;

  return (
    <p className="flex items-center gap-2">
      <span className="text-label text-ink-muted">Ability</span>
      <span className="text-correct-ink font-mono text-mono-xs">
        <span aria-hidden="true">▲</span> +{gain.toFixed(2)}
      </span>
      <span className="sr-only">increased by {gain.toFixed(2)}</span>
    </p>
  );
}
