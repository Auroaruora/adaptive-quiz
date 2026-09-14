"use client";

import { useState } from "react";

import { QuizScreen } from "@/components/quiz/QuizScreen";
import type { Outcome } from "@/components/ui/SegmentedBar";
import { correctFeedback, incorrectFeedback, question } from "@/lib/fixtures";
import type { Feedback } from "@/lib/types";

/**
 * The quiz screen, clickable, running on fixtures.
 *
 * Grading is faked against the fixture's correct option, and the session
 * bar fills with each answer so both colours can be seen.
 */
export default function QuizPreview() {
  const [chosenOptionId, setChosenOptionId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [outcomes, setOutcomes] = useState<Outcome[]>([
    "correct",
    "incorrect",
    "correct",
  ]);

  function submit() {
    if (chosenOptionId === null) return;
    const right = chosenOptionId === correctFeedback.correctOptionId;
    setFeedback(right ? correctFeedback : incorrectFeedback);
  }

  function next() {
    if (feedback) {
      setOutcomes((o) =>
        o.length < 10
          ? [...o, feedback.isCorrect ? "correct" : "incorrect"]
          : o,
      );
    }
    setFeedback(null);
    setChosenOptionId(null);
  }

  return (
    <QuizScreen
      topicName="Logarithms"
      question={question}
      progress={{ step: outcomes.length, of: 10, outcomes }}
      feedback={feedback}
      chosenOptionId={chosenOptionId}
      onSelect={setChosenOptionId}
      onSubmit={submit}
      onNext={next}
    />
  );
}
