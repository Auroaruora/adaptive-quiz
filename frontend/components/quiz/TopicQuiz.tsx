"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { QuizScreen } from "./QuizScreen";
import { TopicComplete } from "@/components/complete/TopicComplete";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { Panel } from "@/components/ui/Panel";
import {
  ApiError,
  getProgress,
  listTopics,
  nextQuestion,
  submitAnswer,
} from "@/lib/api";
import type {
  Feedback,
  NextQuestion,
  Topic,
  TopicProgress,
  User,
} from "@/lib/types";

interface TopicQuizProps {
  user: User;
  slug: string;
}

interface Mastery {
  mastered: number;
  total: number;
}

function describe(e: unknown): string {
  if (e instanceof ApiError && e.status === 0) {
    return "The quiz server is not reachable right now.";
  }
  return e instanceof Error ? e.message : "Something went wrong.";
}

/**
 * One topic's quiz on live data: ask, grade, explain, next.
 *
 * The concept being practised lives in the URL, so a drill can be linked
 * to from the dashboard and survives a reload. Narrowing from one of the
 * question's own chips keeps that question on screen, since it belongs to
 * the new pool; nothing is swapped out from under a half-read stem.
 *
 * Submitting returns the next whole-topic question in the same round trip.
 * That is used as-is when practising everything, and set aside when a
 * concept is being drilled, since only a fresh request can honour the tag.
 */
export function TopicQuiz({ user, slug }: TopicQuizProps) {
  const router = useRouter();
  const pathname = usePathname();
  const tag = useSearchParams().get("tag") || null;

  const [topic, setTopic] = useState<Topic | null>(null);
  const [mastery, setMastery] = useState<Mastery | null>(null);
  const [served, setServed] = useState<NextQuestion | null>(null);
  const [chosen, setChosen] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [pending, setPending] = useState<NextQuestion | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [finished, setFinished] = useState<TopicProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Only the latest request may land; an earlier one that resolves late
  // would put a stale question on screen.
  const generation = useRef(0);
  const ask = useCallback(
    async (topicId: number, forTag: string | null) => {
      const mine = ++generation.current;
      setServed(null);
      try {
        const next = await nextQuestion(user.id, topicId, forTag ?? undefined);
        if (mine === generation.current) setServed(next);
      } catch (e) {
        if (mine === generation.current) setError(describe(e));
      }
    },
    [user.id],
  );

  useEffect(() => {
    let cancelled = false;
    // The URL at the moment of loading, read here rather than through the
    // hook so that later changes to the tag do not reload the topic.
    const initialTag =
      new URLSearchParams(window.location.search).get("tag") || null;
    Promise.all([listTopics(), getProgress(user.id)])
      .then(([topics, progress]) => {
        if (cancelled) return;
        const found = topics.find((t) => t.slug === slug);
        const summary = progress.topics.find((t) => t.slug === slug)?.summary;
        if (!found || !summary) {
          setError(`There is no topic called “${slug}”.`);
          return;
        }
        setTopic(found);
        setMastery({ mastered: summary.mastered, total: summary.total });
        void ask(found.id, initialTag);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(describe(e));
      });
    return () => {
      cancelled = true;
    };
  }, [user.id, slug, ask]);

  useEffect(() => {
    if (!served?.complete || tag !== null) return;
    let cancelled = false;
    getProgress(user.id)
      .then((progress) => {
        const done = progress.topics.find((t) => t.slug === slug);
        if (!cancelled && done) setFinished(done);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(describe(e));
      });
    return () => {
      cancelled = true;
    };
  }, [served, tag, user.id, slug]);

  function replaceTag(next: string | null) {
    const query = next ? `?tag=${encodeURIComponent(next)}` : "";
    router.replace(`${pathname}${query}`, { scroll: false });
  }

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
      // A served question is never already mastered: selection offers
      // unseen questions first and then ones last answered wrong.
      if (result.feedback.isCorrect) {
        setMastery((m) => m && { ...m, mastered: m.mastered + 1 });
      }
    } catch (e) {
      setError(describe(e));
    } finally {
      setSubmitting(false);
    }
  }

  function advance(nextTag: string | null) {
    if (!topic) return;
    setFeedback(null);
    setChosen(null);
    if (nextTag === null && pending) setServed(pending);
    else void ask(topic.id, nextTag);
    setPending(null);
    if (nextTag !== tag) replaceTag(nextTag);
  }

  if (error) return <Notice>{error}</Notice>;
  if (finished) {
    return (
      <TopicComplete
        topic={finished}
        onBack={() => router.push("/")}
        onPractise={(tagSlug) => {
          setFinished(null);
          advance(tagSlug);
        }}
      />
    );
  }
  if (!topic || !mastery || !served) {
    return <Notice muted>Finding your next question…</Notice>;
  }

  if (served.complete) {
    if (tag === null) return <Notice muted>Adding it up…</Notice>;
    return (
      <div className="mx-auto w-full max-w-[720px]">
        <Panel tone="deep">
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-4">
              <Eyebrow tone="onDark">Concept done</Eyebrow>
              <h1 className="text-h2">
                Every question on this concept is answered
              </h1>
              <p className="text-body-lg text-surface/70 max-w-[60ch]">
                The rest of {topic.name} is still waiting.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => advance(null)}
                className="bg-surface text-ink hover:bg-accent-soft text-body cursor-pointer rounded-sm px-8 py-4 font-medium transition-colors"
              >
                Practise everything
              </button>
              <button
                type="button"
                onClick={() => router.push("/")}
                className="border-surface/25 text-surface/80 hover:border-surface hover:text-surface text-body cursor-pointer rounded-sm border px-8 py-4 font-medium transition-colors"
              >
                Back to topics
              </button>
            </div>
          </div>
        </Panel>
      </div>
    );
  }

  return (
    <QuizScreen
      topicName={topic.name}
      question={served.question}
      mastered={mastery.mastered}
      total={mastery.total}
      feedback={feedback}
      chosenOptionId={chosen}
      submitting={submitting}
      onSelect={setChosen}
      onSubmit={submit}
      onNext={() => advance(tag)}
      practising={tag}
      // While asking, a chip only narrows what comes after this question.
      // After answering it also moves on, which is what "practise more of
      // this" means when pressed from the feedback.
      onPractise={(tagSlug) =>
        feedback ? advance(tagSlug) : replaceTag(tagSlug)
      }
      onClearPractice={() => replaceTag(null)}
    />
  );
}
