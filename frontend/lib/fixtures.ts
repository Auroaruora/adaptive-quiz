/**
 * Sample payloads for building and reviewing screens without a backend.
 *
 * Copied from real seeded content and a real /submit-answer response, so
 * the text lengths here are representative rather than convenient.
 */

import type { Feedback, Question } from "./types";

export const question: Question = {
  id: 200,
  topicSlug: "logarithms",
  stem: "Solve for x:  log_3(x) = 4",
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
