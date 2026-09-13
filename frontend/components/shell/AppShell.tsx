"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const NAV = [
  { href: "/preview/dashboard", label: "Dashboard" },
  { href: "/preview/quiz", label: "Quiz" },
  { href: "/preview/complete", label: "Topic complete" },
  { href: "/preview/tokens", label: "Tokens" },
] as const;

interface AppShellProps {
  children: ReactNode;
}

/**
 * The frame every screen sits in.
 *
 * There is no Feedback entry. Feedback is a state of the quiz screen, not
 * a destination, and giving it a tab would imply a student could reach it
 * without having answered anything.
 *
 * The nav is a prototype affordance rather than product navigation. It
 * exists so every screen can be reached while the design is being built,
 * and the PROTOTYPE tag says so plainly.
 */
export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen">
      <header className="border-line bg-bg/80 sticky top-0 z-10 border-b backdrop-blur">
        <div className="mx-auto flex max-w-[1200px] items-center gap-8 px-8 py-4">
          <Link
            href="/preview/dashboard"
            className="flex shrink-0 items-center gap-2"
          >
            <span aria-hidden="true" className="bg-accent h-3 w-3 rounded-sm" />
            <span className="text-title text-ink font-medium">Asymptote</span>
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

          <span className="text-mono-xs text-ink-faint shrink-0 font-mono uppercase">
            Prototype
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-8 py-12">{children}</main>
    </div>
  );
}
