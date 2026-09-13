import { FeedbackPanel } from "./FeedbackPanel";
import { MasteryBar } from "./MasteryBar";
import { OptionList } from "./OptionList";
import { QuestionStem } from "./QuestionStem";
import { TagChips } from "./TagChips";
import type { Feedback, Question } from "@/lib/types";

interface QuizScreenProps {
  topicName: string;
  question: Question;
  mastered: number;
  total: number;
  /** Null while the question is still being asked. */
  feedback: Feedback | null;
  chosenOptionId: number | null;
  onSelect: (optionId: number) => void;
  onSubmit: () => void;
  onNext: () => void;
  /** Slug of the concept being drilled, if practice is narrowed. */
  practising?: string | null;
  onPractise?: (slug: string) => void;
  onClearPractice?: () => void;
}

/**
 * The working screen, in both of its states.
 *
 * Asking and feedback are one screen rather than two routes, so the
 * question and the options stay exactly where they were when the answer
 * lands. Nothing reflows underneath the student between choosing an answer
 * and reading why it was wrong.
 *
 * Purely presentational: every value arrives as a prop, which is what lets
 * it run from fixtures now and from the API later without changing.
 */
export function QuizScreen({
  topicName,
  question,
  mastered,
  total,
  feedback,
  chosenOptionId,
  onSelect,
  onSubmit,
  onNext,
  practising = null,
  onPractise,
  onClearPractice,
}: QuizScreenProps) {
  const answered = feedback !== null;
  const drilled = question.tags.find((t) => t.slug === practising);

  return (
    <div className="mx-auto flex w-full max-w-[720px] flex-col gap-8">
      <header className="flex flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <p className="text-label text-ink-muted">{topicName}</p>
          {drilled && onClearPractice && (
            <p className="text-label text-ink-muted flex items-center gap-3">
              <span>
                Practising <span className="text-ink">{drilled.name}</span>
              </span>
              <button
                type="button"
                onClick={onClearPractice}
                className="text-accent hover:text-accent-press cursor-pointer underline"
              >
                practise everything
              </button>
            </p>
          )}
        </div>
        <MasteryBar mastered={mastered} total={total} />
      </header>

      <div className="flex flex-col gap-4">
        <TagChips
          tags={question.tags}
          active={practising}
          onPractise={onPractise}
        />
        <QuestionStem>{question.stem}</QuestionStem>
      </div>

      <OptionList
        options={question.options}
        chosenOptionId={chosenOptionId}
        correctOptionId={answered ? feedback.correctOptionId : null}
        onSelect={answered ? undefined : onSelect}
      />

      {answered ? (
        <FeedbackPanel feedback={feedback} onNext={onNext} />
      ) : (
        <button
          type="button"
          onClick={onSubmit}
          disabled={chosenOptionId === null}
          className="bg-accent hover:bg-accent-press active:bg-accent-press text-surface text-body disabled:bg-line disabled:text-ink-faint self-start rounded-sm px-6 py-3 font-medium transition-colors enabled:cursor-pointer disabled:cursor-not-allowed"
        >
          Check answer
        </button>
      )}
    </div>
  );
}
