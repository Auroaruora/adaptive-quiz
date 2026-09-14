"use client";

import { Placement } from "@/components/placement/Placement";
import { RequireUser } from "@/components/shell/RequireUser";

export default function PlacementPage() {
  return <RequireUser>{(user) => <Placement user={user} />}</RequireUser>;
}
