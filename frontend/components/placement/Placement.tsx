"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { QuizScreen } from "@/components/quiz/QuizScreen";
import { Notice } from "@/components/ui/Notice";
import { ApiError, listTopics, nextQuestion, submitAnswer } from "@/lib/api";
import type { Feedback, NextQuestion, Topic, User } from "@/lib/types";

/** Questions per topic. Three topics make a twelve-step run. */
const PER_TOPIC = 4;

interface PlacementProps {
  user: User;
}

function describe(e: unknown): string {
  if (e instanceof ApiError && e.status === 0) {
    return "The quiz server is not reachable right now.";
  }
  return e instanceof Error ? e.message : "Something went wrong.";
}

/**
 * The first session: a fixed run of four questions from each topic.
 *
 * There is no placement endpoint. The ordinary next-question selection
 * already starts at the middle of the scale and moves with every answer,
 * so a short run through it is a placement, and the same ability estimate
 * carries straight into practice afterwards. Nothing is special-cased on
 * the backend, which means nothing can drift.
 */
export function Placement({ user }: PlacementProps) {
  const router = useRouter();
  const [topics, setTopics] = useState<Topic[] | null>(null);
  const [step, setStep] = useState(0);
  const [served, setServed] = useState<NextQuestion | null>(null);
  const [chosen, setChosen] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [pending, setPending] = useState<NextQuestion | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const total = topics ? topics.length * PER_TOPIC : 0;
  const topic = topics?.[Math.floor(step / PER_TOPIC)] ?? null;

  useEffect(() => {
    let cancelled = false;
    listTopics()
      .then((list) => {
        if (!cancelled) setTopics(list);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(describe(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!topics) return;
    if (step >= topics.length * PER_TOPIC) {
      router.push("/");
      return;
    }
    if (served) return;
    const current = topics[Math.floor(step / PER_TOPIC)];
    let cancelled = false;
    nextQuestion(user.id, current.id)
      .then((next) => {
        if (cancelled) return;
        // A topic with nothing left to ask cannot place anyone; move on.
        if (next.complete)
          setStep(Math.ceil((step + 1) / PER_TOPIC) * PER_TOPIC);
        else setServed(next);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(describe(e));
      });
    return () => {
      cancelled = true;
    };
  }, [topics, step, served, user.id, router]);

  async function submit() {
    if (!served || served.complete || chosen === null || submitting) return;
    setSubmitting(true);
    try {
      const result = await submitAnswer({
        userId: user.id,
        questionId: served.question.id,
        selectedOptionId: chosen,
      });
      setFeedback(result.feedback);
      setPending(result.next);
    } catch (e) {
      setError(describe(e));
    } finally {
      setSubmitting(false);
    }
  }

  function next() {
    const following = step + 1;
    const sameTopic = following % PER_TOPIC !== 0;
    setFeedback(null);
    setChosen(null);
    // The answer's own response carries the next question of this topic;
    // crossing into the next topic needs a fresh request.
    setServed(sameTopic && pending && !pending.complete ? pending : null);
    setPending(null);
    setStep(following);
  }

  if (error) return <Notice>{error}</Notice>;
  if (!topics || !topic || !served || served.complete) {
    return <Notice muted>Finding your next question…</Notice>;
  }

  return (
    <QuizScreen
      topicName={topic.name}
      question={served.question}
      mastered={0}
      total={0}
      feedback={feedback}
      chosenOptionId={chosen}
      submitting={submitting}
      onSelect={setChosen}
      onSubmit={submit}
      onNext={next}
      placement={{ step, of: total }}
    />
  );
}
