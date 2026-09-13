interface MisconceptionNoteProps {
  children: string;
}

/**
 * Names the specific error behind the option the student picked.
 *
 * This is the thing the product exists to do, so it leads the feedback and
 * sits above the general solution. The heading is phrased as an
 * observation rather than a verdict — the student already knows they were
 * wrong, and repeating it teaches nothing.
 */
export function MisconceptionNote({ children }: MisconceptionNoteProps) {
  return (
    <section className="rounded-md border border-incorrect bg-incorrect-soft p-4">
      <h2 className="text-label text-incorrect-ink mb-2 font-medium">
        What happened here
      </h2>
      <p className="text-body-lg text-incorrect-ink">{children}</p>
    </section>
  );
}
