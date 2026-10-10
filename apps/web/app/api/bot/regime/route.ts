import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

function num(value: unknown): number | null {
  if (value == null) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const botName = searchParams.get('bot') || searchParams.get('botName') || 'quantshift-equity';

    let row: Record<string, unknown> | null = null;
    try {
      const rows = await prisma.$queryRaw<Record<string, unknown>[]>`
        SELECT regime, method, confidence, risk_multiplier, allocation, timestamp,
               trend_slope, volatility, market_breadth, vix
        FROM regime_history
        WHERE bot_name = ${botName}
          AND timestamp > NOW() - INTERVAL '3 days'
        ORDER BY timestamp DESC
        LIMIT 1
      `;
      row = rows[0] ?? null;
    } catch (columnError) {
      console.error('Regime query fell back to the original columns:', columnError);
      const rows = await prisma.$queryRaw<Record<string, unknown>[]>`
        SELECT regime, method, confidence, risk_multiplier, allocation, timestamp
        FROM regime_history
        WHERE bot_name = ${botName}
          AND timestamp > NOW() - INTERVAL '3 days'
        ORDER BY timestamp DESC
        LIMIT 1
      `;
      row = rows[0] ?? null;
    }

    if (!row) {
      return NextResponse.json({ regime: null });
    }

    const allocation = typeof row.allocation === 'string'
      ? JSON.parse(row.allocation)
      : row.allocation;

    return NextResponse.json({
      regime: row.regime,
      confidence: num(row.confidence),
      trend: num(row.trend_slope),
      volatility: num(row.volatility),
      marketBreadth: num(row.market_breadth),
      vix: num(row.vix),
      method: row.method,
      riskMultiplier: num(row.risk_multiplier) ?? 1,
      risk_multiplier: num(row.risk_multiplier) ?? 1,
      allocation,
      timestamp: row.timestamp,
    });
  } catch (error) {
    console.error('Error fetching regime data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch regime data' },
      { status: 500 }
    );
  }
}
