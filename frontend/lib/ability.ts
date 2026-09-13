/**
 * Presenting ability to students.
 *
 * Theta stays the model's unit and the API's. This maps it onto 0–100 for
 * display only — a student cannot act on "θ 1.18", but they can act on
 * "65, up 24 this week". Nothing here feeds back into the model.
 */

import type { SeriesPoint } from "./types";

/** The range the update rule clamps theta to. */
const MIN = -4;
const MAX = 4;

export function abilityScore(theta: number): number {
  const clamped = Math.min(MAX, Math.max(MIN, theta));
  return Math.round(((clamped - MIN) / (MAX - MIN)) * 100);
}

/**
 * Change in score over a trailing window.
 *
 * Returns null when there is nothing to compare against — a first session
 * has no "this week", and inventing a rise from a single point would be a
 * lie dressed as encouragement.
 */
export function scoreChange(series: SeriesPoint[], days = 7): number | null {
  if (series.length < 2) return null;

  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  const withinWindow = series.filter((p) => Date.parse(p.at) >= cutoff);
  if (withinWindow.length < 2) return null;

  const first = withinWindow[0];
  const last = withinWindow[withinWindow.length - 1];
  const change = abilityScore(last.theta) - abilityScore(first.theta);
  return change === 0 ? null : change;
}
