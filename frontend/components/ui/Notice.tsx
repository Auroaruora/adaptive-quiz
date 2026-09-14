import type { ReactNode } from "react";

interface NoticeProps {
  children: ReactNode;
  /** For waiting states, which should not read as something gone wrong. */
  muted?: boolean;
}

/** A single line of status where a screen would otherwise be. */
export function Notice({ children, muted = false }: NoticeProps) {
  return (
    <p
      role={muted ? "status" : "alert"}
      className={`text-body-lg py-12 text-center ${muted ? "text-ink-faint" : "text-ink-muted"}`}
    >
      {children}
    </p>
  );
}
