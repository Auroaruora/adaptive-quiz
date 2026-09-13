"use client";

import { FeedbackPanel } from "@/components/quiz/FeedbackPanel";
import { OptionList } from "@/components/quiz/OptionList";
import { QuestionStem } from "@/components/quiz/QuestionStem";
import {
  chosenWrongOptionId,
  correctFeedback,
  incorrectFeedback,
  question,
} from "@/lib/fixtures";

/**
 * Renders both feedback states side by side for review.
 *
 * Development only — not a screen in the product, and not linked from
 * anywhere. It exists so the two states can be compared directly, which is
 * the only way to tell whether they read as help rather than as a verdict.
 */
export default function FeedbackPreview() {
  return (
    <main className="mx-auto flex max-w-[1100px] flex-col gap-12 p-8">
      <header>
        <p className="text-label text-ink-faint font-mono">PREVIEW</p>
        <h1 className="text-h2 text-ink">Feedback states</h1>
      </header>

      <div className="grid gap-12 md:grid-cols-2">
        <section className="flex flex-col gap-6">
          <h2 className="text-label text-ink-muted font-medium">
            Answered correctly
          </h2>
          <QuestionStem>{question.stem}</QuestionStem>
          <OptionList
            options={question.options}
            chosenOptionId={correctFeedback.correctOptionId}
            correctOptionId={correctFeedback.correctOptionId}
          />
          <FeedbackPanel feedback={correctFeedback} onNext={() => {}} />
        </section>

        <section className="flex flex-col gap-6">
          <h2 className="text-label text-ink-muted font-medium">
            Answered incorrectly
          </h2>
          <QuestionStem>{question.stem}</QuestionStem>
          <OptionList
            options={question.options}
            chosenOptionId={chosenWrongOptionId}
            correctOptionId={incorrectFeedback.correctOptionId}
          />
          <FeedbackPanel feedback={incorrectFeedback} onNext={() => {}} />
        </section>
      </div>
    </main>
  );
}
