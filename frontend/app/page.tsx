"use client";

import { DashboardPage } from "@/components/dashboard/DashboardPage";
import { RequireUser } from "@/components/shell/RequireUser";

export default function Home() {
  return <RequireUser>{(user) => <DashboardPage user={user} />}</RequireUser>;
}
