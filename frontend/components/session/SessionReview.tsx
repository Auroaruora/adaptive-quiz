"use client";

import { useState } from "react";

import { QuizScreen } from "@/components/quiz/QuizScreen";
import type { AnswerRecord } from "@/lib/types";

interface SessionReviewProps {
  /** The wrong answers, in the order they were given. */
  records: readonly AnswerRecord[];
  onDone: () => void;
}

/**
 * Walks back through the questions a session got wrong.
 *
 * Each is shown exactly as it was at the moment of feedback: the chosen
 * option marked, the correct one marked, the misconception and the steps.
 * Nothing is re-answered and nothing is sent to the backend; the session
 * already has everything it needs to show.
 */
export function SessionReview({ records, onDone }: SessionReviewProps) {
  const [index, setIndex] = useState(0);
  const record = records[index];
  if (!record) return null;
  const last = index === records.length - 1;

  return (
    <QuizScreen
      topicName={record.topic.name}
      mode="Review"
      question={record.question}
      progress={{ step: index, of: records.length, outcomes: [] }}
      feedback={record.feedback}
      chosenOptionId={record.chosenOptionId}
      onSelect={() => {}}
      onSubmit={() => {}}
      onNext={() => (last ? onDone() : setIndex(index + 1))}
      nextLabel={last ? "Back to the summary" : "Next one"}
    />
  );
}
