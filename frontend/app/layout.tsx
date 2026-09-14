import type { Metadata } from "next";
import { IBM_Plex_Mono, Instrument_Sans, Newsreader } from "next/font/google";
import "./globals.css";

import { AppShell } from "@/components/shell/AppShell";
import { UserProvider } from "@/components/shell/UserProvider";

const sans = Instrument_Sans({
  variable: "--font-instrument-sans",
  subsets: ["latin"],
});

// IBM Plex Mono is not a variable font, so weights are listed explicitly.
const mono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

// Italic only: mathematical variables are conventionally set in italic
// serif, and this family is used for nothing else.
const math = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  style: ["italic"],
});

export const metadata: Metadata = {
  title: "Adaptive Quiz",
  description:
    "Practice calculus with questions matched to your current ability.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${sans.variable} ${mono.variable} ${math.variable}`}
    >
      <body>
        <UserProvider>
          <AppShell>{children}</AppShell>
        </UserProvider>
      </body>
    </html>
  );
}
