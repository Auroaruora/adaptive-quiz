import type { Tag } from "@/lib/types";

interface TagChipsProps {
  tags: Tag[];
}

/**
 * The concepts a question exercises, as chips.
 *
 * Labels, not buttons. They used to narrow practice when pressed, but
 * changing what a session is about halfway through it undermined the
 * session; that choice now belongs to the board at the end. Shown as chips
 * rather than a caption so they still read as the concepts the board will
 * offer.
 *
 * Capped at three. Beyond that the row wraps and stops being scannable,
 * and the API already orders them rarest first, so the three shown are
 * the most specific.
 */
export function TagChips({ tags }: TagChipsProps) {
  return (
    <ul className="flex list-none flex-wrap items-center gap-2">
      {tags.slice(0, 3).map((tag) => (
        <li key={tag.slug}>
          <span className="text-label bg-surface border-line text-ink-muted inline-block rounded-full border px-3 py-1">
            {tag.name}
          </span>
        </li>
      ))}
    </ul>
  );
}
