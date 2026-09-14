"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { SessionBoard } from "./SessionBoard";
import { SessionReview } from "./SessionReview";
import { TopicComplete } from "@/components/complete/TopicComplete";
import { QuizScreen } from "@/components/quiz/QuizScreen";
import { Notice } from "@/components/ui/Notice";
import type { Outcome } from "@/components/ui/SegmentedBar";
import { ApiError, getProgress, nextQuestion, submitAnswer } from "@/lib/api";
import type {
  AnswerRecord,
  Feedback,
  NextQuestion,
  Progress,
  Question,
  Topic,
  User,
} from "@/lib/types";

/** One stretch of a session: up to `take` questions from one pool. */
export interface SessionSource {
  topic: Topic;
  take: number;
  /** Narrows the pool to these concepts. Empty means the whole topic. */
  tags?: readonly string[];
}

interface SessionProps {
  user: User;
  /** Must be referentially stable; a new array starts a new session. */
  sources: readonly SessionSource[];
  /** Shown in the header: "Placement". Omit for practice. */
  mode?: string;
  onExit: () => void;
  onPractise: (topic: Topic, tags: string[]) => void;
}

type Phase = "asking" | "board" | "review" | "summary";

function describe(e: unknown): string {
  if (e instanceof ApiError && e.status === 0) {
    return "The quiz server is not reachable right now.";
  }
  return e instanceof Error ? e.message : "Something went wrong.";
}

/**
 * One sitting: a fixed run of questions, then a board.
 *
 * Every question asked is passed back as an exclusion, so nothing repeats
 * within the session however the backend's tiers fall. A pool that runs
 * short ends the session early rather than looping; the board says so.
 * Placement and practice differ only in their sources: four from each
 * topic, or up to ten from one topic or set of concepts.
 *
 * Bookkeeping that the screen never shows, such as which ids have been
 * served, lives in refs; what it shows lives in state.
 */
export function Session({
  user,
  sources,
  mode,
  onExit,
  onPractise,
}: SessionProps) {
  const [phase, setPhase] = useState<Phase>("asking");
  const [current, setCurrent] = useState<{
    question: Question;
    topic: Topic;
  } | null>(null);
  const [chosen, setChosen] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [pending, setPending] = useState<NextQuestion | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [records, setRecords] = useState<AnswerRecord[]>([]);
  const [planned, setPlanned] = useState(() =>
    sources.reduce((n, s) => n + s.take, 0),
  );
  const [progress, setProgress] = useState<Progress | null>(null);
  const [summaryOf, setSummaryOf] = useState<Topic | null>(null);
  const [error, setError] = useState<string | null>(null);

  const served = useRef<Record<number, number[]>>({});
  const sourceIndex = useRef(0);
  const askedInSource = useRef(0);
  // Only the latest request may land; an earlier one resolving late would
  // put a stale question on screen.
  const generation = useRef(0);

  const ask = useCallback(async () => {
    const mine = ++generation.current;
    setCurrent(null);
    for (;;) {
      const source = sources[sourceIndex.current];
      if (!source) {
        setPhase("board");
        return;
      }
      const exclude = served.current[source.topic.id] ?? [];
      try {
        const next = await nextQuestion(user.id, source.topic.id, {
          tags: source.tags,
          exclude,
        });
        if (mine !== generation.current) return;
        if (next.complete) {
          // The pool ran short: shorten the run instead of looping.
          setPlanned((n) => n - (source.take - askedInSource.current));
          sourceIndex.current += 1;
          askedInSource.current = 0;
          continue;
        }
        served.current[source.topic.id] = [...exclude, next.question.id];
        setCurrent({ question: next.question, topic: source.topic });
        return;
      } catch (e) {
        if (mine === generation.current) setError(describe(e));
        return;
      }
    }
  }, [user.id, sources]);

  // Ask once on mount. Strict mode runs effects twice in development, and
  // a second ask would serve two questions for one step.
  const started = useRef(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void ask();
  }, [ask]);

  useEffect(() => {
    if (phase !== "board" || progress) return;
    let cancelled = false;
    getProgress(user.id)
      .then((p) => {
        if (!cancelled) setProgress(p);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(describe(e));
      });
    return () => {
      cancelled = true;
    };
  }, [phase, progress, user.id]);

  async function submit() {
    if (!current || chosen === null || submitting) return;
    setSubmitting(true);
    try {
      const result = await submitAnswer({
        userId: user.id,
        questionId: current.question.id,
        selectedOptionId: chosen,
      });
      setFeedback(result.feedback);
      setPending(result.next);
      setRecords((r) => [
        ...r,
        {
          question: current.question,
          topic: current.topic,
          chosenOptionId: chosen,
          feedback: result.feedback,
        },
      ]);
      askedInSource.current += 1;
    } catch (e) {
      setError(describe(e));
    } finally {
      setSubmitting(false);
    }
  }

  function next() {
    setFeedback(null);
    setChosen(null);
    const before = sources[sourceIndex.current];
    if (askedInSource.current >= before.take) {
      sourceIndex.current += 1;
      askedInSource.current = 0;
    }
    const source = sources[sourceIndex.current];
    const exclude = source ? (served.current[source.topic.id] ?? []) : [];
    // The answer's own response carries a next whole-topic question. It
    // saves a round trip when it fits the pool and has not been asked.
    const reusable =
      source === before &&
      !source.tags?.length &&
      pending !== null &&
      !pending.complete &&
      !exclude.includes(pending.question.id);
    setPending(null);
    if (reusable && source) {
      served.current[source.topic.id] = [...exclude, pending.question.id];
      setCurrent({ question: pending.question, topic: source.topic });
    } else {
      void ask();
    }
  }

  const outcomes: Outcome[] = records.map((r) =>
    r.feedback.isCorrect ? "correct" : "incorrect",
  );

  if (error) return <Notice>{error}</Notice>;

  if (phase === "summary" && summaryOf && progress) {
    const topic = progress.topics.find((t) => t.slug === summaryOf.slug);
    if (topic) {
      return (
        <TopicComplete
          topic={topic}
          onBack={onExit}
          onPractise={(tag) => onPractise(summaryOf, [tag])}
        />
      );
    }
  }

  if (phase === "review") {
    return (
      <SessionReview
        records={records.filter((r) => !r.feedback.isCorrect)}
        onDone={() => setPhase("board")}
      />
    );
  }

  if (phase === "board" || phase === "summary") {
    if (!progress) return <Notice muted>Adding it up…</Notice>;
    return (
      <SessionBoard
        mode={mode}
        records={records}
        planned={sources.reduce((n, s) => n + s.take, 0)}
        progress={progress}
        onReview={() => setPhase("review")}
        onPractise={onPractise}
        onSummary={(topic) => {
          setSummaryOf(topic);
          setPhase("summary");
        }}
        onBack={onExit}
      />
    );
  }

  if (!current) return <Notice muted>Finding your next question…</Notice>;

  return (
    <QuizScreen
      topicName={current.topic.name}
      mode={mode}
      question={current.question}
      // While feedback shows, the question on screen is still the one just
      // answered, so the counter stays on it.
      progress={{
        step: records.length - (feedback ? 1 : 0),
        of: planned,
        outcomes,
      }}
      feedback={feedback}
      chosenOptionId={chosen}
      submitting={submitting}
      onSelect={setChosen}
      onSubmit={submit}
      onNext={next}
      nextLabel={records.length >= planned ? "See how you did" : undefined}
    />
  );
}
