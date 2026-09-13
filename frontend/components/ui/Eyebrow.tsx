interface EyebrowProps {
  children: string;
  /** A small dot before the label, for drawing the eye to one of several. */
  dot?: "accent" | "incorrect" | "correct";
  tone?: "muted" | "faint" | "accent" | "onDark";
}

const TONE = {
  muted: "text-ink-muted",
  faint: "text-ink-faint",
  accent: "text-accent",
  onDark: "text-accent",
} as const;

const DOT = {
  accent: "bg-accent",
  incorrect: "bg-incorrect",
  correct: "bg-correct",
} as const;

/**
 * A mono, uppercase label above a heading.
 *
 * Does the work of a subheading without adding another size to the type
 * scale, which is most of what makes the layout read as deliberate rather
 * than merely stacked.
 */
export function Eyebrow({ children, dot, tone = "muted" }: EyebrowProps) {
  return (
    <p
      className={`text-mono-xs flex items-center gap-2 font-mono uppercase ${TONE[tone]}`}
    >
      {dot && (
        <span
          aria-hidden="true"
          className={`h-2 w-2 rounded-full ${DOT[dot]}`}
        />
      )}
      {children}
    </p>
  );
}
