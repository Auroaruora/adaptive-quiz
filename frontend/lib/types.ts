/**
 * Mirrors of the API payloads in docs/api.md.
 *
 * A question being asked deliberately carries no answer-revealing fields —
 * the backend withholds them until an answer is submitted, and these types
 * make that split visible rather than leaving it to convention.
 */

export type AbilityLevel =
  "developing" | "progressing" | "proficient" | "advanced";

export interface Topic {
  id: number;
  slug: string;
  name: string;
  description: string;
  /** Active questions only, so a retired one stops being advertised. */
  questionCount: number;
}

export interface User {
  id: number;
  displayName: string;
  createdAt: string;
}

export interface Option {
  id: number;
  text: string;
  position: number;
}

/** A concept a question exercises. */
export interface Tag {
  slug: string;
  name: string;
}

export interface Question {
  id: number;
  topicSlug: string;
  stem: string;
  /** Rarest first, so showing only the first shows the most specific. */
  tags: Tag[];
  options: Option[];
}

export interface Ability {
  theta: number;
  level: AbilityLevel;
}

/**
 * What both quiz endpoints return. The question is null exactly when the
 * pool is complete, and the union makes that a checked branch rather than a
 * convention: narrowing on `complete` is the only way to reach the question.
 */
export type NextQuestion =
  | {
      question: Question;
      ability: Ability;
      complete: false;
      /** Questions the pool could still serve, counting this one. */
      remaining: number;
    }
  | { question: null; ability: Ability; complete: true; remaining: 0 };

export interface Feedback {
  isCorrect: boolean;
  correctOptionId: number;
  /** Populated only for a wrong answer. */
  misconception: string | null;
  solution: string[];
  thetaBefore: number;
  thetaAfter: number;
}

/** One round trip: the grade for this answer and the question after it. */
export interface AnswerResult {
  feedback: Feedback;
  next: NextQuestion;
}

/** Everything a session keeps about one answered question. */
export interface AnswerRecord {
  question: Question;
  topic: Topic;
  chosenOptionId: number;
  feedback: Feedback;
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

/** A concept the student is currently getting wrong. */
export interface WeakSpot {
  slug: string;
  name: string;
  missed: number;
}

export interface TopicProgress {
  slug: string;
  name: string;
  summary: TopicSummary;
  /** Worst first. Empty when nothing has been answered incorrectly. */
  weakSpots: WeakSpot[];
  series: SeriesPoint[];
}

export interface Progress {
  userId: number;
  topics: TopicProgress[];
}
