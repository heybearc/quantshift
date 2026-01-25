'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface Bot {
  name: string;
  status: string;
  positions: number;
  heartbeat: string | null;
  state: any;
  lastUpdate: string | null;
}

export default function BotsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBots = async () => {
      try {
        const res = await fetch('/api/bots');
        const data = await res.json();
        setBots(data.bots || []);
      } catch (error) {
        console.error('Error fetching bots:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBots();
    const interval = setInterval(fetchBots, 5000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Bot Status</h1>
            <p className="text-slate-400">Monitor bot health and performance</p>
          </div>
          <Link href="/" className="px-4 py-2 bg-slate-700 text-white rounded hover:bg-slate-600">
            ← Back to Dashboard
          </Link>
        </div>

        {loading ? (
          <div className="text-center text-white py-12">Loading bots...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {bots.map((bot) => (
              <Card key={bot.name} className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-white text-2xl">
                        {bot.name.replace('-bot', '').toUpperCase()}
                      </CardTitle>
                      <CardDescription className="text-slate-400">
                        {bot.name}
                      </CardDescription>
                    </div>
                    <div className={`px-3 py-1 rounded text-sm font-semibold ${
                      bot.status === 'running' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {bot.status}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-slate-400 text-sm">Open Positions</p>
                        <p className="text-white font-semibold text-xl">{bot.positions}</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Heartbeat</p>
                        <p className="text-white font-semibold text-sm">
                          {bot.heartbeat 
                            ? new Date(bot.heartbeat).toLocaleTimeString()
                            : 'N/A'
                          }
                        </p>
                      </div>
                    </div>

                    {bot.state && Object.keys(bot.state).length > 0 && (
                      <div className="border-t border-slate-700 pt-4">
                        <p className="text-slate-400 text-sm mb-2">Bot State</p>
                        <div className="bg-slate-900 rounded p-3">
                          <pre className="text-slate-300 text-xs overflow-auto">
                            {JSON.stringify(bot.state, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}

                    {bot.lastUpdate && (
                      <p className="text-slate-500 text-xs">
                        Last update: {new Date(bot.lastUpdate).toLocaleString()}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
