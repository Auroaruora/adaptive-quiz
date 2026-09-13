/**
 * Shown above the topic cards until a student has answered anything.
 *
 * Three cards of zeros explain nothing on their own — a new student has no
 * reason to know what an ability estimate is or why the questions change.
 * This says it once, in the place where it is the only thing to read, and
 * then never appears again.
 *
 * Deliberately not a separate screen: the topics stay visible underneath,
 * so the panel reads as an introduction rather than a gate.
 */
export function WelcomePanel() {
  return (
    <section className="border-line bg-surface shadow-raised flex flex-col gap-4 rounded-xl border p-8">
      <h2 className="text-h2 text-ink">Start anywhere</h2>

      <p className="text-body-lg text-ink-muted max-w-[60ch]">
        Every question is picked to sit just at the edge of what you can already
        do. Answer a few and the difficulty moves to meet you — upward when you
        are getting them right, gently back when you are not.
      </p>

      <p className="text-body-lg text-ink-muted max-w-[60ch]">
        Get one wrong and you will be told exactly which mistake it was, not
        just that it was wrong. Questions you miss come back later; a topic is
        finished once you have answered all eighteen correctly.
      </p>
    </section>
  );
}
