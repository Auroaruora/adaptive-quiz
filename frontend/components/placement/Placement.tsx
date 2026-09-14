"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Session, type SessionSource } from "@/components/session/Session";
import { practiceHref } from "@/components/session/TopicSession";
import { Notice } from "@/components/ui/Notice";
import { ApiError, listTopics } from "@/lib/api";
import type { Topic, User } from "@/lib/types";

/** Questions per topic. Three topics make a twelve-step run. */
const PER_TOPIC = 4;

interface PlacementProps {
  user: User;
}

/**
 * The first session: four questions from each topic, then the board.
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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listTopics()
      .then((list) => {
        if (!cancelled) setTopics(list);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(
          e instanceof ApiError && e.status === 0
            ? "The quiz server is not reachable right now."
            : "The topics could not be loaded.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const sources = useMemo<SessionSource[] | null>(
    () => topics?.map((topic) => ({ topic, take: PER_TOPIC })) ?? null,
    [topics],
  );

  if (error) return <Notice>{error}</Notice>;
  if (!sources) return <Notice muted>Finding your next question…</Notice>;

  return (
    <Session
      user={user}
      sources={sources}
      mode="Placement"
      onExit={() => router.push("/")}
      onPractise={(topic, tags) => router.push(practiceHref(topic.slug, tags))}
    />
  );
}
