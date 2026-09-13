/**
 * Sample payloads for building and reviewing screens without a backend.
 *
 * Copied from real seeded content and a real /submit-answer response, so
 * the text lengths here are representative rather than convenient.
 */

import type {
  Feedback,
  Progress,
  Question,
  SeriesPoint,
  TopicProgress,
} from "./types";

export const question: Question = {
  id: 200,
  topicSlug: "logarithms",
  stem: "Solve for x:  log_3(x) = 4",
  tags: [
    { slug: "log-equation", name: "Log equation" },
    { slug: "log-definition", name: "Log definition" },
    { slug: "logarithmic", name: "Logarithmic" },
  ],
  options: [
    { id: 424, text: "64", position: 1 },
    { id: 425, text: "81", position: 2 },
    { id: 426, text: "12", position: 3 },
    { id: 427, text: "7", position: 4 },
  ],
};

const solution = [
  "Rewrite the logarithm in exponential form.",
  "log_3(x) = 4 means 3^4 = x.",
  "3^4 = 81, so x = 81.",
];

export const correctFeedback: Feedback = {
  isCorrect: true,
  correctOptionId: 425,
  misconception: null,
  solution,
  thetaBefore: 0.0,
  thetaAfter: 0.15,
};

export const incorrectFeedback: Feedback = {
  isCorrect: false,
  correctOptionId: 425,
  misconception:
    "That is 4^3. The base is 3 and the exponent is 4, so it is 3^4, not 4^3.",
  solution,
  thetaBefore: 0.0,
  thetaAfter: -0.15,
};

/** The option the student picked in `incorrectFeedback`. */
export const chosenWrongOptionId = 424;

/** Builds a plausible answer series, so sparklines have real shape. */
function series(thetas: number[], wrongAt: number[] = []): SeriesPoint[] {
  const start = Date.parse("2026-09-13T16:00:00Z");
  return thetas.map((theta, i) => ({
    at: new Date(start + i * 90_000).toISOString(),
    theta,
    isCorrect: !wrongAt.includes(i),
  }));
}

export const populatedProgress: Progress = {
  userId: 7,
  topics: [
    {
      slug: "derivatives",
      name: "Derivatives",
      summary: {
        theta: -0.42,
        level: "progressing",
        answered: 9,
        correct: 4,
        mastered: 4,
        total: 18,
      },
      weakSpots: [
        { slug: "chain-rule", name: "Chain rule", missed: 3 },
        { slug: "product-rule", name: "Product rule", missed: 2 },
        { slug: "power-rule", name: "Power rule", missed: 1 },
      ],
      series: series(
        [-0.15, -0.31, -0.14, -0.3, -0.45, -0.28, -0.44, -0.58, -0.42],
        [0, 1, 3, 4, 6, 7],
      ),
    },
    {
      slug: "logarithms",
      name: "Logarithms",
      summary: {
        theta: 1.18,
        level: "proficient",
        answered: 14,
        correct: 11,
        mastered: 11,
        total: 18,
      },
      weakSpots: [
        { slug: "extraneous-root", name: "Extraneous root", missed: 2 },
        { slug: "change-of-base", name: "Change of base", missed: 1 },
      ],
      series: series(
        [
          0.15, 0.29, 0.13, 0.31, 0.48, 0.63, 0.5, 0.67, 0.82, 0.95, 1.06, 0.92,
          1.05, 1.18,
        ],
        [2, 6, 11],
      ),
    },
    {
      slug: "trigonometry",
      name: "Trigonometry",
      summary: {
        theta: 0.0,
        level: "progressing",
        answered: 0,
        correct: 0,
        mastered: 0,
        total: 18,
      },
      weakSpots: [],
      series: [],
    },
  ],
};

/** What a brand-new student sees: three topics, nothing answered. */
export const emptyProgress: Progress = {
  userId: 8,
  topics: populatedProgress.topics.map((topic) => ({
    ...topic,
    summary: {
      ...topic.summary,
      theta: 0,
      level: "progressing",
      answered: 0,
      correct: 0,
      mastered: 0,
    },
    weakSpots: [],
    series: [],
  })),
};

/** A finished topic, for the completion screen. */
export const completedTopic: TopicProgress = {
  slug: "logarithms",
  name: "Logarithms",
  summary: {
    theta: 1.43,
    level: "proficient",
    answered: 23,
    correct: 18,
    mastered: 18,
    total: 18,
  },
  weakSpots: [],
  series: series(
    [
      0.15, 0.29, 0.13, 0.31, 0.48, 0.63, 0.5, 0.67, 0.82, 0.95, 1.06, 0.92,
      1.05, 1.18, 1.09, 1.21, 1.32, 1.2, 1.31, 1.41, 1.3, 1.4, 1.43,
    ],
    [2, 6, 11, 14, 17],
  ),
};
