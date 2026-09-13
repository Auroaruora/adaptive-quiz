"use client";

import { TopicComplete } from "@/components/complete/TopicComplete";
import { completedTopic } from "@/lib/fixtures";

/** The completion screen, on a finished fixture topic. */
export default function CompletePreview() {
  return (
    <main className="flex flex-col gap-8 p-8">
      <header className="mx-auto w-full max-w-[720px]">
        <p className="text-label text-ink-faint font-mono">PREVIEW</p>
        <h1 className="text-h2 text-ink">Completion screen</h1>
      </header>

      <TopicComplete topic={completedTopic} onBack={() => {}} />
    </main>
  );
}
