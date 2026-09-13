import { Eyebrow } from "@/components/ui/Eyebrow";
import type { WeakSpot } from "@/lib/types";

interface WeakSpotsProps {
  spots: WeakSpot[];
  started: boolean;
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
 */
export function WeakSpots({ spots, started }: WeakSpotsProps) {
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
            <li key={spot.slug} className="flex items-baseline gap-3">
              <span
                aria-hidden="true"
                className="bg-incorrect mt-2 h-2 w-2 shrink-0 rounded-full"
              />
              <span className="text-body text-ink grow">{spot.name}</span>
              <span className="text-ink-muted shrink-0 font-mono text-mono-xs">
                {spot.missed}&times;
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
