import { Eyebrow } from "@/components/ui/Eyebrow";
import type { WeakSpot } from "@/lib/types";

interface WeakSpotsProps {
  spots: WeakSpot[];
  started: boolean;
  onPractise: (tagSlug: string) => void;
}

/**
 * The concepts a student is currently getting wrong, worst first.
 *
 * This replaced a chart of ability over time. A rising line described
 * difficulty-matching, which is no longer what the app is for, and a
 * student could not act on it. A named concept with a count is the same
 * information turned into something to do.
 *
 * The order is the backend's, which is the same decayed ranking that
 * decides what the quiz serves next — so this names what is coming rather
 * than offering a second opinion about it.
 *
 * Each row is a button. Naming a weakness and then making the student go
 * find it themselves would waste the only thing this panel knows.
 */
export function WeakSpots({ spots, started, onPractise }: WeakSpotsProps) {
  return (
    // `grow` so the block absorbs the difference between a card with
    // three weak spots and one with none, keeping the mastery bar and
    // button aligned across the row.
    <div className="flex grow flex-col gap-3">
      <Eyebrow tone="faint">Weak spots</Eyebrow>

      {spots.length === 0 ? (
        <p className="text-body text-ink-faint">
          {started ? "Nothing outstanding" : "Nothing yet"}
        </p>
      ) : (
        <ul className="flex list-none flex-col gap-2">
          {spots.map((spot) => (
            <li key={spot.slug}>
              <button
                type="button"
                onClick={() => onPractise(spot.slug)}
                title={`Practise ${spot.name} only`}
                className="hover:bg-accent-soft group -mx-2 flex w-full cursor-pointer items-baseline gap-3 rounded-sm px-2 py-1 text-left transition-colors"
              >
                <span
                  aria-hidden="true"
                  className="bg-incorrect mt-2 h-2 w-2 shrink-0 rounded-full"
                />
                <span className="text-body text-ink group-hover:text-accent grow">
                  {spot.name}
                </span>
                <span className="text-ink-muted shrink-0 font-mono text-mono-xs">
                  {spot.missed}&times;
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
