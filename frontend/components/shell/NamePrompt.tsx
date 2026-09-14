"use client";

import { useState, type FormEvent } from "react";

import { Eyebrow } from "@/components/ui/Eyebrow";
import { Panel } from "@/components/ui/Panel";
import { ApiError, createUser } from "@/lib/api";
import type { User } from "@/lib/types";

interface NamePromptProps {
  onCreated: (user: User) => void;
}

/**
 * Asks for a name on first visit.
 *
 * Not a screen: there is no route, no account and no password. It is the
 * one dark panel of whichever page needed a student and found none, and
 * it disappears the moment there is one.
 */
export function NamePrompt({ onCreated }: NamePromptProps) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setError(null);
    try {
      onCreated(await createUser(trimmed));
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 0
          ? "The quiz server is not reachable right now."
          : "That name could not be saved. Try another.",
      );
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-[720px]">
      <Panel tone="deep">
        <form onSubmit={submit} className="flex flex-col gap-6">
          <div className="flex flex-col gap-4">
            <Eyebrow tone="onDark">Before you start</Eyebrow>
            <h1 className="text-h2">What should we call you?</h1>
            <p className="text-body-lg text-surface/70 max-w-[60ch]">
              There is no account to make. A name is enough to keep your
              progress on this device.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <label className="sr-only" htmlFor="display-name">
              Your name
            </label>
            <input
              id="display-name"
              name="displayName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={50}
              autoComplete="given-name"
              autoFocus
              placeholder="Your name"
              className="bg-surface text-ink placeholder:text-ink-faint text-body-lg grow rounded-sm px-4 py-3"
            />
            <button
              type="submit"
              disabled={busy || name.trim() === ""}
              className="bg-accent hover:bg-accent-press active:bg-accent-press text-surface text-body disabled:bg-surface/15 disabled:text-surface/50 shrink-0 rounded-sm px-8 py-3 font-medium transition-colors enabled:cursor-pointer disabled:cursor-not-allowed"
            >
              {busy ? "Saving…" : "Start"}
            </button>
          </div>

          {error && (
            <p role="alert" className="text-body text-surface/80">
              {error}
            </p>
          )}
        </form>
      </Panel>
    </div>
  );
}
