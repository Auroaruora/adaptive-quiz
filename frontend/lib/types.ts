/**
 * Mirrors of the API payloads in docs/api.md.
 *
 * A question being asked deliberately carries no answer-revealing fields —
 * the backend withholds them until an answer is submitted, and these types
 * make that split visible rather than leaving it to convention.
 */

export type AbilityLevel =
  "developing" | "progressing" | "proficient" | "advanced";

export interface Option {
  id: number;
  text: string;
  position: number;
}

export interface Question {
  id: number;
  topicSlug: string;
  stem: string;
  options: Option[];
}

export interface Ability {
  theta: number;
  level: AbilityLevel;
}

export interface Feedback {
  isCorrect: boolean;
  correctOptionId: number;
  /** Populated only for a wrong answer. */
  misconception: string | null;
  solution: string[];
  thetaBefore: number;
  thetaAfter: number;
}

/** How one option should render once an answer has been submitted. */
export type OptionState =
  "idle" | "selected" | "correct" | "incorrect" | "muted";

export interface TopicSummary {
  theta: number;
  level: AbilityLevel;
  answered: number;
  correct: number;
  mastered: number;
  total: number;
}

export interface SeriesPoint {
  at: string;
  theta: number;
  isCorrect: boolean;
}

export interface TopicProgress {
  slug: string;
  name: string;
  summary: TopicSummary;
  series: SeriesPoint[];
}

export interface Progress {
  userId: number;
  topics: TopicProgress[];
}
