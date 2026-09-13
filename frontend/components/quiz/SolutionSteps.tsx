interface SolutionStepsProps {
  steps: string[];
  /** Collapsed by default after a correct answer. */
  defaultOpen?: boolean;
}

/**
 * The worked solution, one line per step.
 *
 * Collapsible because a student who answered correctly does not need the
 * method spelled out, but may still want to check their reasoning. After a
 * wrong answer it opens by default, following the misconception.
 *
 * Set in sans, not the math family. Steps read as sentences that happen to
 * contain expressions — "Rewrite the logarithm in exponential form." is
 * prose, and italic serif makes it look like a quotation.
 */
export function SolutionSteps({
  steps,
  defaultOpen = true,
}: SolutionStepsProps) {
  return (
    <details open={defaultOpen} className="group">
      <summary className="text-label text-ink-muted hover:text-ink cursor-pointer list-none font-medium">
        <span className="group-open:hidden">Show the steps</span>
        <span className="hidden group-open:inline">Hide the steps</span>
      </summary>

      <ol className="mt-3 flex list-none flex-col gap-3">
        {steps.map((step, index) => (
          <li key={step} className="flex gap-3">
            <span
              aria-hidden="true"
              className="text-ink-faint font-mono text-mono-xs pt-1"
            >
              {index + 1}
            </span>
            <span className="text-body-lg text-ink">{step}</span>
          </li>
        ))}
      </ol>
    </details>
  );
}
