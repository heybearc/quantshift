import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

type PredictionRow = {
  regime_ml: string;
  regime_rule_based: string;
  actual_regime: string | null;
  ml_confidence: number | null;
};

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const botName = new URL(request.url).searchParams.get('botName') || 'quantshift-equity';

    let rows: PredictionRow[] = [];
    try {
      rows = await prisma.$queryRaw<PredictionRow[]>`
        SELECT regime_ml, regime_rule_based, actual_regime, ml_confidence
        FROM regime_predictions
        WHERE bot_name = ${botName}
          AND validated = TRUE
          AND actual_regime IS NOT NULL
          AND timestamp >= NOW() - INTERVAL '30 days'
      `;
    } catch (queryError) {
      console.error('Regime accuracy table is not available:', queryError);
      return NextResponse.json({ available: false, total_predictions: 0 });
    }

    if (rows.length === 0) {
      return NextResponse.json({ available: false, total_predictions: 0 });
    }

    const total = rows.length;
    const mlCorrect = rows.filter((row) => row.regime_ml === row.actual_regime).length;
    const ruleCorrect = rows.filter((row) => row.regime_rule_based === row.actual_regime).length;
    const mlAccuracy = (mlCorrect / total) * 100;
    const ruleAccuracy = (ruleCorrect / total) * 100;
    const highConfidence = rows.filter((row) => (row.ml_confidence ?? 0) > 0.8);
    const highConfidenceCorrect = highConfidence.filter((row) => row.regime_ml === row.actual_regime).length;
    const highConfidenceAccuracy = highConfidence.length
      ? (highConfidenceCorrect / highConfidence.length) * 100
      : 0;

    return NextResponse.json({
      available: true,
      total_predictions: total,
      ml_accuracy: mlAccuracy,
      rule_accuracy: ruleAccuracy,
      ml_better: mlAccuracy > ruleAccuracy,
      accuracy_difference: mlAccuracy - ruleAccuracy,
      high_confidence_accuracy: highConfidenceAccuracy,
    });
  } catch (error) {
    console.error('Error fetching regime accuracy:', error);
    return NextResponse.json(
      { error: 'Failed to fetch regime accuracy' },
      { status: 500 }
    );
  }
}
