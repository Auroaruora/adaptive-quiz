"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Session, type SessionSource } from "./Session";
import { Notice } from "@/components/ui/Notice";
import { ApiError, listTopics } from "@/lib/api";
import type { Topic, User } from "@/lib/types";

/** Questions in one practice session, when the pool has that many. */
export const SESSION_LENGTH = 10;

interface TopicSessionProps {
  user: User;
  slug: string;
}

/** Builds the URL for a practice session, narrowed to concepts if given. */
export function practiceHref(slug: string, tags: readonly string[] = []) {
  const query = tags.length
    ? `?tags=${encodeURIComponent(tags.join(","))}`
    : "";
  return `/quiz/${slug}${query}`;
}

/**
 * A practice session in one topic.
 *
 * The concepts being drilled live in the URL, so a drill can be linked to
 * from the dashboard or the board and survives a reload. Changing them
 * starts a new session: the Session is keyed on them.
 */
export function TopicSession({ user, slug }: TopicSessionProps) {
  const router = useRouter();
  const tagsParam = useSearchParams().get("tags") ?? "";
  const [topic, setTopic] = useState<Topic | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listTopics()
      .then((topics) => {
        if (cancelled) return;
        const found = topics.find((t) => t.slug === slug);
        if (found) setTopic(found);
        else setError(`There is no topic called “${slug}”.`);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(
          e instanceof ApiError && e.status === 0
            ? "The quiz server is not reachable right now."
            : "The topic could not be loaded.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  const sources = useMemo<SessionSource[] | null>(() => {
    if (!topic) return null;
    const tags = tagsParam.split(",").filter(Boolean);
    return [{ topic, take: SESSION_LENGTH, tags }];
  }, [topic, tagsParam]);

  if (error) return <Notice>{error}</Notice>;
  if (!sources) return <Notice muted>Finding your next question…</Notice>;

  return (
    <Session
      key={`${slug}:${tagsParam}`}
      user={user}
      sources={sources}
      onExit={() => router.push("/")}
      onPractise={(t, tags) => router.push(practiceHref(t.slug, tags))}
    />
  );
}
