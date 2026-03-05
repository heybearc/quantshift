import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: Request) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const botName = searchParams.get('botName') || 'quantshift-equity';

    // Mock data for now - will be replaced with actual data from strategy_automation_manager
    const mockStatus = [
      {
        strategy_name: 'BollingerBounce',
        enabled: true,
        performance_metrics: {
          win_rate: 0.552,
          sharpe: 1.45,
          trades: 45,
        },
      },
      {
        strategy_name: 'RSIMeanReversion',
        enabled: true,
        performance_metrics: {
          win_rate: 0.487,
          sharpe: 1.12,
          trades: 38,
        },
      },
      {
        strategy_name: 'BreakoutMomentum',
        enabled: false,
        disabled_reason: 'Win rate too low: 32% < 40%',
        disabled_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        performance_metrics: {
          win_rate: 0.32,
          sharpe: 0.35,
          trades: 25,
        },
      },
    ];

    return NextResponse.json(mockStatus);
  } catch (error) {
    console.error('Error fetching strategy status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch strategy status' },
      { status: 500 }
    );
  }
}
