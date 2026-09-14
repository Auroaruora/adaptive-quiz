/**
 * Remembering who the student is between visits.
 *
 * There is no authentication by design, so identity is a user id and a
 * display name kept in this browser. Losing it costs nothing but a fresh
 * name prompt, and a remembered id the backend no longer knows is handled
 * the same way.
 *
 * Exposed as an external store so React can subscribe to it: the server
 * snapshot is "unknown", which is what lets a returning student's first
 * render wait for storage instead of flashing the prompt.
 */

import type { User } from "./types";

const USER_KEY = "adaptive-quiz.user";
const PLACEMENT_KEY = "adaptive-quiz.placement-dismissed";

const listeners = new Set<() => void>();

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function notify(): void {
  listeners.forEach((listener) => listener());
}

function parse(raw: string | null): User | null {
  if (!raw) return null;
  try {
    const value: unknown = JSON.parse(raw);
    if (
      typeof value === "object" &&
      value !== null &&
      typeof (value as User).id === "number" &&
      typeof (value as User).displayName === "string"
    ) {
      return value as User;
    }
  } catch {
    // Unreadable: treat as absent.
  }
  return null;
}

let cachedRaw: string | null = null;
let cachedUser: User | null = null;

/** Stable between reads of the same stored value, as React requires. */
export function getUserSnapshot(): User | null {
  const raw = storage()?.getItem(USER_KEY) ?? null;
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    cachedUser = parse(raw);
  }
  return cachedUser;
}

export function getUserServerSnapshot(): undefined {
  return undefined;
}

export function subscribeUser(listener: () => void): () => void {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

export function saveUser(user: User): void {
  storage()?.setItem(USER_KEY, JSON.stringify(user));
  notify();
}

/** Forgets the user and everything remembered about their session. */
export function clearUser(): void {
  storage()?.removeItem(USER_KEY);
  storage()?.removeItem(PLACEMENT_KEY);
  notify();
}

export function loadPlacementDismissed(): boolean {
  return storage()?.getItem(PLACEMENT_KEY) === "1";
}

export function savePlacementDismissed(): void {
  storage()?.setItem(PLACEMENT_KEY, "1");
}
