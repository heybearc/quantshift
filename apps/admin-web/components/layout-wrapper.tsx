'use client';

import { Navigation } from './navigation';

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-50">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
