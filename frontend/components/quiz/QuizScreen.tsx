import { FeedbackPanel } from "./FeedbackPanel";
import { MasteryBar } from "./MasteryBar";
import { OptionList } from "./OptionList";
import { QuestionStem } from "./QuestionStem";
import { Eyebrow } from "@/components/ui/Eyebrow";
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
}: QuizScreenProps) {
  const answered = feedback !== null;

  return (
    <div className="mx-auto flex w-full max-w-[720px] flex-col gap-8">
      <header className="flex flex-col gap-4">
        <p className="text-label text-ink-muted">{topicName}</p>
        <MasteryBar mastered={mastered} total={total} />
      </header>

      <div className="flex flex-col gap-3">
        {/*
          One tag, the first, which the API orders rarest first — so this
          is the most specific concept the question exercises. Showing all
          of them would bury that under "polynomial", which is true of
          nearly every question in the topic.
        */}
        {question.tags[0] && (
          <Eyebrow tone="faint">{question.tags[0].name}</Eyebrow>
        )}
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
