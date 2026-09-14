"use client";

import { useParams } from "next/navigation";
import { Suspense } from "react";

import { TopicSession } from "@/components/session/TopicSession";
import { RequireUser } from "@/components/shell/RequireUser";
import { Notice } from "@/components/ui/Notice";

/**
 * The session reads its concepts from the query string, and Next requires
 * a Suspense boundary above anything that does so the rest of the page
 * can still be prerendered.
 */
export default function QuizPage() {
  const { topic } = useParams<{ topic: string }>();

  return (
    <RequireUser>
      {(user) => (
        <Suspense fallback={<Notice muted>Finding your next question…</Notice>}>
          <TopicSession user={user} slug={topic} />
        </Suspense>
      )}
    </RequireUser>
  );
}
