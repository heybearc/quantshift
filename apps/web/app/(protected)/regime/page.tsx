'use client';

import { RegimeDashboard } from '@/components/regime-dashboard-simple';
import { ProtectedRoute } from '@/components/protected-route';
import { LayoutWrapper } from '@/components/layout-wrapper';

export default function RegimePage() {
  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="flex-1 space-y-4 p-8 pt-6 bg-slate-900 min-h-screen">
          <div className="flex items-center justify-between space-y-2">
            <div>
              <h2 className="text-3xl font-bold tracking-tight text-white">Market Regime Analysis</h2>
              <p className="text-slate-400">
                ML-powered regime detection with 91.7% accuracy
              </p>
            </div>
          </div>
          <RegimeDashboard />
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  );
}
