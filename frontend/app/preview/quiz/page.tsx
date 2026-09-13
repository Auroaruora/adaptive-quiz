"use client";

import { useState } from "react";

import { QuizScreen } from "@/components/quiz/QuizScreen";
import { correctFeedback, incorrectFeedback, question } from "@/lib/fixtures";
import type { Feedback } from "@/lib/types";

/**
 * The quiz screen, clickable, running on fixtures.
 *
 * Grading is faked against the fixture's correct option so the
 * ask-answer-feedback loop can be walked through before it is wired up.
 */
export default function QuizPreview() {
  const [chosenOptionId, setChosenOptionId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [mastered, setMastered] = useState(7);

  function submit() {
    if (chosenOptionId === null) return;
    const right = chosenOptionId === correctFeedback.correctOptionId;
    setFeedback(right ? correctFeedback : incorrectFeedback);
    if (right) setMastered((n) => Math.min(n + 1, 18));
  }

  function next() {
    setFeedback(null);
    setChosenOptionId(null);
  }

  return (
    <QuizScreen
      topicName="Logarithms"
      question={question}
      mastered={mastered}
      total={18}
      feedback={feedback}
      chosenOptionId={chosenOptionId}
      onSelect={setChosenOptionId}
      onSubmit={submit}
      onNext={next}
    />
  );
}
