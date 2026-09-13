interface SolutionStepsProps {
  steps: string[];
}

/**
 * The worked solution, one line per step.
 *
 * Always collapsed to begin with, including after a wrong answer. The
 * misconception above already says what went wrong, and unfolding a full
 * method underneath it turns a short correction into a wall of text. A
 * student who wants the method asks for it.
 *
 * Set in sans, not the math family. Steps read as sentences that happen to
 * contain expressions — "Rewrite the logarithm in exponential form." is
 * prose, and italic serif makes it look like a quotation.
 */
export function SolutionSteps({ steps }: SolutionStepsProps) {
  return (
    <details className="group">
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
