/**
 * Presenting ability to students.
 *
 * Ability shown is the share of questions answered correctly in a topic,
 * not the model's theta. A student can act on "you get two in three
 * right"; they cannot act on a logit, and theta describes how the app
 * picks questions rather than how well they are doing.
 *
 * Theta still exists and still breaks ties in selection. It is simply not
 * what gets shown.
 */

import type { AbilityLevel, TopicSummary } from "./types";

/**
 * Percentage of answers that were correct.
 *
 * Null when nothing has been answered — a topic with no attempts has no
 * accuracy, and rendering it as 0 would read as a score of nothing rather
 * than an absence of data.
 */
export function accuracy(summary: TopicSummary): number | null {
  if (summary.answered === 0) return null;
  return Math.round((summary.correct / summary.answered) * 100);
}

/** Thresholds are inclusive lower bounds, in percent. */
const BANDS: ReadonlyArray<readonly [number, AbilityLevel]> = [
  [90, "advanced"],
  [70, "proficient"],
  [50, "progressing"],
  [0, "developing"],
];

export function accuracyLevel(percent: number): AbilityLevel {
  return BANDS.find(([floor]) => percent >= floor)![1];
}
