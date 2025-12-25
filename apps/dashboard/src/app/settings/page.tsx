'use client';

import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Settings</h1>
            <p className="text-slate-400">Configure your trading platform</p>
          </div>
          <Link href="/" className="px-4 py-2 bg-slate-700 text-white rounded hover:bg-slate-600">
            ← Back to Dashboard
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Bot Configuration</CardTitle>
              <CardDescription className="text-slate-400">
                Coming soon - Configure bot parameters and strategies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-slate-500">
                Bot settings under development
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Risk Management</CardTitle>
              <CardDescription className="text-slate-400">
                Coming soon - Set risk limits and position sizing rules
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-slate-500">
                Risk settings under development
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">Notifications</CardTitle>
              <CardDescription className="text-slate-400">
                Coming soon - Configure alerts and notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-slate-500">
                Notification settings under development
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
