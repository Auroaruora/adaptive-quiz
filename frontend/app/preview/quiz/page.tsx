"use client";

import { useState } from "react";

import { QuizScreen } from "@/components/quiz/QuizScreen";
import { correctFeedback, incorrectFeedback, question } from "@/lib/fixtures";
import type { Feedback } from "@/lib/types";

/**
 * The quiz screen, clickable, running on fixtures.
 *
 * Development only. Grading is faked against the fixture's correct option
 * so the ask-answer-feedback loop can be walked through before any of it
 * is wired to the API.
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
    <main className="flex flex-col gap-8 p-8">
      <header className="mx-auto w-full max-w-[720px]">
        <p className="text-label text-ink-faint font-mono">PREVIEW</p>
        <h1 className="text-h2 text-ink">Quiz screen</h1>
        <p className="text-body text-ink-muted mt-2">
          Pick an option and check it. Option B is the correct answer.
        </p>
      </header>

      <QuizScreen
        topicName="Logarithms &amp; Exponentials"
        question={question}
        mastered={mastered}
        total={18}
        feedback={feedback}
        chosenOptionId={chosenOptionId}
        onSelect={setChosenOptionId}
        onSubmit={submit}
        onNext={next}
      />
    </main>
  );
}
