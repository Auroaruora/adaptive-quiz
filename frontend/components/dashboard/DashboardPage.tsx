"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Dashboard } from "./Dashboard";
import { useUser } from "@/components/shell/UserProvider";
import { Notice } from "@/components/ui/Notice";
import { ApiError, getProgress } from "@/lib/api";
import type { Progress, User } from "@/lib/types";
import { loadPlacementDismissed, savePlacementDismissed } from "@/lib/user";

interface DashboardPageProps {
  user: User;
}

/**
 * The dashboard on live data.
 *
 * A remembered id the backend no longer knows comes back as a 404. That is
 * not an error to show; it means the database was reset under a returning
 * browser, so the student is simply asked for a name again.
 */
export function DashboardPage({ user }: DashboardPageProps) {
  const router = useRouter();
  const { forget } = useUser();
  const [progress, setProgress] = useState<Progress | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Safe to read storage here: this renders only once the user is known,
  // which never happens on the server.
  const [dismissed, setDismissed] = useState(loadPlacementDismissed);

  useEffect(() => {
    let cancelled = false;
    getProgress(user.id)
      .then((p) => {
        if (!cancelled) setProgress(p);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 404) {
          forget();
        } else {
          setError("Your progress could not be loaded.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [user.id, forget]);

  if (error) return <Notice>{error}</Notice>;
  if (!progress) return <Notice muted>Loading your topics…</Notice>;

  return (
    <Dashboard
      progress={progress}
      placementDismissed={dismissed}
      onStart={(slug) => router.push(`/quiz/${slug}`)}
      onPractise={(slug, tag) =>
        router.push(`/quiz/${slug}?tag=${encodeURIComponent(tag)}`)
      }
      onBeginPlacement={() => router.push("/placement")}
      onSkipPlacement={() => {
        savePlacementDismissed();
        setDismissed(true);
      }}
    />
  );
}
