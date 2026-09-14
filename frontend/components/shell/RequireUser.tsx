"use client";

import type { ReactNode } from "react";

import { NamePrompt } from "./NamePrompt";
import { useUser } from "./UserProvider";
import type { User } from "@/lib/types";

interface RequireUserProps {
  children: (user: User) => ReactNode;
}

/**
 * Renders its children only once there is a student to render them for.
 *
 * Nothing is drawn while storage is being read, so a returning student
 * never glimpses the name prompt on the way to their dashboard.
 *
 * The children are a function, so any page using this must itself be a
 * client component: a function cannot cross from a server page.
 */
export function RequireUser({ children }: RequireUserProps) {
  const { user, ready, remember } = useUser();

  if (!ready) return null;
  if (!user) return <NamePrompt onCreated={remember} />;
  return <>{children(user)}</>;
}
