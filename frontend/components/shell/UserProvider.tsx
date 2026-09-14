"use client";

import {
  createContext,
  useContext,
  useMemo,
  useSyncExternalStore,
  type ReactNode,
} from "react";

import {
  clearUser,
  getUserServerSnapshot,
  getUserSnapshot,
  saveUser,
  subscribeUser,
} from "@/lib/user";
import type { User } from "@/lib/types";

interface UserContextValue {
  /** Null until storage has been read, and again after forgetting. */
  user: User | null;
  /** False on the server and during hydration, before storage is read. */
  ready: boolean;
  remember: (user: User) => void;
  forget: () => void;
}

const UserContext = createContext<UserContextValue | null>(null);

/**
 * Holds the remembered student for the whole app.
 *
 * Storage is subscribed to rather than copied into state, so the server
 * and the first client render agree, and a page that needs the user waits
 * for `ready` instead of flashing the name prompt at a returning student.
 */
export function UserProvider({ children }: { children: ReactNode }) {
  const snapshot = useSyncExternalStore(
    subscribeUser,
    getUserSnapshot,
    getUserServerSnapshot,
  );

  const value = useMemo<UserContextValue>(
    () => ({
      user: snapshot ?? null,
      ready: snapshot !== undefined,
      remember: saveUser,
      forget: clearUser,
    }),
    [snapshot],
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser(): UserContextValue {
  const value = useContext(UserContext);
  if (!value) throw new Error("useUser needs a UserProvider above it");
  return value;
}
