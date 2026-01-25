"use client";

import { Suspense } from "react";
import AcceptInvitationContent from "./content";

export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <AcceptInvitationContent />
    </Suspense>
  );
}
