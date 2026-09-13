import { AppShell } from "@/components/shell/AppShell";

/** Wraps every preview screen in the product shell. */
export default function PreviewLayout({ children }: LayoutProps<"/preview">) {
  return <AppShell>{children}</AppShell>;
}
