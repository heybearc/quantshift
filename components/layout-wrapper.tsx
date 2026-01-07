"use client";

import { Navigation } from "./navigation";
import { ReleaseBanner } from "./release-banner";
import { useAuth } from "@/lib/auth-context";

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        {children}
      </main>
    </div>
  );
}
