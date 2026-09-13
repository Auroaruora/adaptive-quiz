import type { Option, OptionState } from "@/lib/types";

const LETTERS = ["A", "B", "C", "D"];

const SHELL: Record<OptionState, string> = {
  idle: "bg-surface border-line text-ink shadow-raised hover:border-accent hover:bg-accent-soft active:bg-accent-soft active:border-accent-press",
  selected: "bg-accent-soft border-accent text-ink shadow-raised",
  correct: "bg-correct-soft border-correct text-correct-ink",
  incorrect: "bg-incorrect-soft border-incorrect text-incorrect-ink",
  muted: "bg-surface border-line text-ink-faint",
};

const BADGE: Record<OptionState, string> = {
  idle: "border-line text-ink-muted",
  selected: "border-accent text-accent",
  correct: "border-correct text-correct-ink",
  incorrect: "border-incorrect text-incorrect-ink",
  muted: "border-line text-ink-faint",
};

function CorrectMark() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className="h-4 w-4">
      <path
        d="M3.5 8.5l3 3 6-7"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IncorrectMark() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className="h-4 w-4">
      <path
        d="M4.5 4.5l7 7M11.5 4.5l-7 7"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

interface OptionButtonProps {
  option: Option;
  state: OptionState;
  /** Omitted once an answer is submitted, which makes the option static. */
  onSelect?: (optionId: number) => void;
}

/**
 * One answer choice.
 *
 * After an answer is submitted the options stop being controls, so they
 * render as plain elements rather than disabled buttons — a disabled
 * button still announces itself as a control that exists but is off,
 * which is not what has happened here.
 *
 * The mark and the wording carry the outcome alongside colour, never
 * colour alone.
 */
export function OptionButton({ option, state, onSelect }: OptionButtonProps) {
  const shared =
    "flex w-full items-center gap-3 rounded-md border p-4 text-left " +
    "transition-colors";
  const outcome =
    state === "correct"
      ? "Correct answer"
      : state === "incorrect"
        ? "Your answer, incorrect"
        : null;

  const content = (
    <>
      <span
        aria-hidden="true"
        className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border font-mono text-mono-xs ${BADGE[state]}`}
      >
        {LETTERS[option.position - 1] ?? option.position}
      </span>

      <span className="font-math text-body-lg grow">{option.text}</span>

      {state === "correct" && <CorrectMark />}
      {state === "incorrect" && <IncorrectMark />}
      {outcome && <span className="sr-only">{outcome}</span>}
    </>
  );

  if (!onSelect) {
    return <div className={`${shared} ${SHELL[state]}`}>{content}</div>;
  }

  return (
    <button
      type="button"
      onClick={() => onSelect(option.id)}
      className={`${shared} ${SHELL[state]} cursor-pointer`}
    >
      {content}
    </button>
  );
}
