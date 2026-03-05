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

    // Mock data for now - will be replaced with actual data from regime_accuracy_tracker
    const mockAccuracy = {
      total_predictions: 127,
      ml_accuracy: 91.7,
      rule_accuracy: 78.3,
      ml_better: true,
      accuracy_difference: 13.4,
      high_confidence_accuracy: 95.2,
    };

    return NextResponse.json(mockAccuracy);
  } catch (error) {
    console.error('Error fetching regime accuracy:', error);
    return NextResponse.json(
      { error: 'Failed to fetch regime accuracy' },
      { status: 500 }
    );
  }
}
