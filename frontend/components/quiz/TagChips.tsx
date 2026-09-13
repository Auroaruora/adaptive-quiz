import type { Tag } from "@/lib/types";

interface TagChipsProps {
  tags: Tag[];
  /** The one currently being practised, if any. */
  active?: string | null;
  onPractise?: (slug: string) => void;
}

/**
 * The concepts a question exercises, as chips.
 *
 * Shown as objects rather than a label, because they are things you can
 * act on — clicking one narrows practice to that concept. A quiet mono
 * eyebrow said the same words but read as a caption, so nobody tried to
 * press it.
 *
 * Capped at three. Beyond that the row wraps and stops being scannable,
 * and the API already orders them rarest first, so the three shown are
 * the most specific.
 */
export function TagChips({ tags, active, onPractise }: TagChipsProps) {
  return (
    <ul className="flex list-none flex-wrap items-center gap-2">
      {tags.slice(0, 3).map((tag) => {
        const isActive = tag.slug === active;
        const shell = isActive
          ? "bg-accent-soft border-accent text-accent"
          : "bg-surface border-line text-ink-muted";

        if (!onPractise) {
          return (
            <li key={tag.slug}>
              <span
                className={`text-label inline-block rounded-full border px-3 py-1 ${shell}`}
              >
                {tag.name}
              </span>
            </li>
          );
        }

        return (
          <li key={tag.slug}>
            <button
              type="button"
              onClick={() => onPractise(tag.slug)}
              aria-pressed={isActive}
              title={`Practise ${tag.name} only`}
              className={`text-label hover:border-accent hover:text-accent cursor-pointer rounded-full border px-3 py-1 transition-colors ${shell}`}
            >
              {tag.name}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
