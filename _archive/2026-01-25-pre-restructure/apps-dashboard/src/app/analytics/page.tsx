'use client';

import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Analytics</h1>
            <p className="text-slate-400">Performance metrics and insights</p>
          </div>
          <Link href="/" className="px-4 py-2 bg-slate-700 text-white rounded hover:bg-slate-600">
            ← Back to Dashboard
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Performance Overview</CardTitle>
              <CardDescription className="text-slate-400">
                Coming soon - Performance charts and metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-slate-500">
                Analytics dashboard under development
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Risk Metrics</CardTitle>
              <CardDescription className="text-slate-400">
                Coming soon - Risk analysis and drawdown metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-slate-500">
                Risk analytics under development
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
