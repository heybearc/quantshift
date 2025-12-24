'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface Position {
  bot: string;
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price?: number;
  stop_loss?: number;
  take_profit?: number;
  unrealized_pnl?: number;
  last_update?: string;
}

export default function PositionsPage() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const res = await fetch('/api/positions');
        const data = await res.json();
        setPositions(data.positions || []);
      } catch (error) {
        console.error('Error fetching positions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPositions();
    const interval = setInterval(fetchPositions, 5000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Open Positions</h1>
            <p className="text-slate-400">Monitor and manage current positions</p>
          </div>
          <Link href="/" className="px-4 py-2 bg-slate-700 text-white rounded hover:bg-slate-600">
            ← Back to Dashboard
          </Link>
        </div>

        {loading ? (
          <div className="text-center text-white py-12">Loading positions...</div>
        ) : positions.length === 0 ? (
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="py-12 text-center">
              <p className="text-slate-400 text-lg">No open positions</p>
              <p className="text-slate-500 text-sm mt-2">Positions will appear here when bots open trades</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {positions.map((position, idx) => (
              <Card key={idx} className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-white text-2xl">{position.symbol}</CardTitle>
                      <CardDescription className="text-slate-400">
                        {position.bot} • {position.quantity} shares
                      </CardDescription>
                    </div>
                    <div className={`px-3 py-1 rounded text-sm font-semibold ${
                      (position.unrealized_pnl || 0) >= 0 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {position.unrealized_pnl 
                        ? `${position.unrealized_pnl >= 0 ? '+' : ''}$${position.unrealized_pnl.toFixed(2)}`
                        : 'N/A'
                      }
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-slate-400 text-sm">Entry Price</p>
                      <p className="text-white font-semibold">${position.entry_price.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-sm">Current Price</p>
                      <p className="text-white font-semibold">
                        ${position.current_price?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-sm">Stop Loss</p>
                      <p className="text-white font-semibold">
                        ${position.stop_loss?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-sm">Take Profit</p>
                      <p className="text-white font-semibold">
                        ${position.take_profit?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                  </div>
                  {position.last_update && (
                    <p className="text-slate-500 text-xs mt-4">
                      Last updated: {new Date(position.last_update).toLocaleString()}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
