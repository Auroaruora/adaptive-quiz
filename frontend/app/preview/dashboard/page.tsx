"use client";

import { useState } from "react";

import { Dashboard } from "@/components/dashboard/Dashboard";
import { emptyProgress, populatedProgress } from "@/lib/fixtures";

/**
 * The dashboard in both states.
 *
 * The welcome panel is driven by the data, not a flag, so the only way to
 * review it is to switch the data underneath. Hence the toggle.
 */
export default function DashboardPreview() {
  const [fresh, setFresh] = useState(true);

  return (
    <main className="flex flex-col gap-8 p-8">
      <header className="mx-auto flex w-full max-w-[1100px] items-end justify-between gap-4">
        <div>
          <p className="text-label text-ink-faint font-mono">PREVIEW</p>
          <h1 className="text-h2 text-ink">Dashboard</h1>
        </div>
        <button
          type="button"
          onClick={() => setFresh((v) => !v)}
          className="border-line text-ink hover:border-accent hover:text-accent text-body cursor-pointer rounded-sm border px-6 py-3 font-medium transition-colors"
        >
          {fresh ? "Show a started account" : "Show a new account"}
        </button>
      </header>

      <Dashboard
        displayName="Aurora"
        progress={fresh ? emptyProgress : populatedProgress}
        onStart={() => {}}
      />
    </main>
  );
}
