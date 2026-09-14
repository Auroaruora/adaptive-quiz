"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useUser } from "./UserProvider";

const NAV = [
  { href: "/", label: "Topics" },
  { href: "/preview/tokens", label: "Tokens" },
] as const;

interface AppShellProps {
  children: ReactNode;
}

/**
 * The frame every screen sits in.
 *
 * The quiz has no pill. It is reached from a topic card, not from the nav,
 * and a pill would imply it could be opened without choosing a topic.
 * Tokens is the design system and stays reachable while the PROTOTYPE tag
 * is up, which says plainly what this is.
 *
 * The student's name is the only sign-in there is, so "not you?" is the
 * only sign-out: it forgets the id on this device and asks again.
 */
export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const { user, forget } = useUser();

  return (
    <div className="min-h-screen">
      <header className="border-line bg-bg/80 sticky top-0 z-10 border-b backdrop-blur">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-x-8 gap-y-2 px-8 py-4">
          <Link href="/" className="flex shrink-0 items-center gap-2">
            <span aria-hidden="true" className="bg-accent h-3 w-3 rounded-sm" />
            <span className="text-title text-ink font-medium">Gradient</span>
          </Link>

          <nav className="flex grow flex-wrap items-center gap-1">
            {NAV.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`text-body rounded-sm px-4 py-2 font-medium transition-colors ${
                    active
                      ? "bg-ink text-surface"
                      : "text-ink-muted hover:text-ink"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {user && (
            <p className="text-label text-ink-muted flex shrink-0 items-baseline gap-2">
              <span className="text-ink">{user.displayName}</span>
              <button
                type="button"
                onClick={forget}
                className="hover:text-accent cursor-pointer underline"
              >
                not you?
              </button>
            </p>
          )}

          <span className="text-mono-xs text-ink-faint shrink-0 font-mono uppercase">
            Prototype
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-8 py-12">{children}</main>
    </div>
  );
}
