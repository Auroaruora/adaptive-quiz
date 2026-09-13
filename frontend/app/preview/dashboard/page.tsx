"use client";

import { useState } from "react";

import { Dashboard } from "@/components/dashboard/Dashboard";
import { emptyProgress, populatedProgress } from "@/lib/fixtures";

export default function DashboardPreview() {
  const [fresh, setFresh] = useState(true);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => setFresh((v) => !v)}
          className="border-line text-ink-muted hover:border-accent hover:text-accent text-label cursor-pointer rounded-sm border px-4 py-2 font-medium transition-colors"
        >
          {fresh ? "Show a placed account" : "Show a new account"}
        </button>
      </div>

      <Dashboard
        progress={fresh ? emptyProgress : populatedProgress}
        onStart={() => {}}
        onBeginPlacement={() => {}}
        onSkipPlacement={() => {}}
      />
    </div>
  );
}
