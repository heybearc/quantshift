import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: Request) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Mock data for now - will be replaced with actual data from optimization_scheduler
    const mockHistory = [
      {
        timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        strategy_name: 'BollingerBounce',
        current_params: { bb_period: 20, bb_std: 2.0, rsi_threshold: 40 },
        optimal_params: { bb_period: 25, bb_std: 2.5, rsi_threshold: 35 },
        train_sharpe: 1.45,
        test_sharpe: 1.62,
        improvement_pct: 11.7,
        applied: true,
      },
      {
        timestamp: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
        strategy_name: 'RSIMeanReversion',
        current_params: { rsi_period: 14, rsi_oversold: 30, rsi_overbought: 70 },
        optimal_params: { rsi_period: 14, rsi_oversold: 35, rsi_overbought: 65 },
        train_sharpe: 1.23,
        test_sharpe: 1.38,
        improvement_pct: 12.2,
        applied: true,
      },
    ];

    return NextResponse.json(mockHistory);
  } catch (error) {
    console.error('Error fetching optimization history:', error);
    return NextResponse.json(
      { error: 'Failed to fetch optimization history' },
      { status: 500 }
    );
  }
}
