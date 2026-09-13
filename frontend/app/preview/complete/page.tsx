"use client";

import { TopicComplete } from "@/components/complete/TopicComplete";
import { completedTopic } from "@/lib/fixtures";

/** The completion screen, on a finished fixture topic. */
export default function CompletePreview() {
  return <TopicComplete topic={completedTopic} onBack={() => {}} />;
}
