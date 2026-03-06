import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/sentiment
 * 
 * Get current sentiment scores for all active symbols
 * Returns sentiment data from bot's in-memory cache via Redis
 */
export async function GET(request: NextRequest) {
  try {
    // TODO: Add authentication when needed
    // For now, this is internal-only and behind the dashboard auth

    // For now, return mock sentiment data
    // TODO: Connect to Redis to get real sentiment from bots
    const mockSentiment = {
      'SPY': { score: 0.65, label: 'Positive', confidence: 0.82, articles: 12, updated: new Date().toISOString() },
      'QQQ': { score: 0.45, label: 'Positive', confidence: 0.75, articles: 8, updated: new Date().toISOString() },
      'AAPL': { score: 0.32, label: 'Positive', confidence: 0.68, articles: 15, updated: new Date().toISOString() },
      'MSFT': { score: 0.58, label: 'Positive', confidence: 0.79, articles: 10, updated: new Date().toISOString() },
      'GOOGL': { score: -0.15, label: 'Negative', confidence: 0.62, articles: 7, updated: new Date().toISOString() },
      'BTC-USD': { score: 0.72, label: 'Positive', confidence: 0.85, articles: 20, updated: new Date().toISOString() },
      'ETH-USD': { score: 0.55, label: 'Positive', confidence: 0.78, articles: 14, updated: new Date().toISOString() },
      'XBTUSD': { score: 0.68, label: 'Positive', confidence: 0.83, articles: 18, updated: new Date().toISOString() },
    };

    return NextResponse.json({ sentiment: mockSentiment });
  } catch (error) {
    console.error('Sentiment API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch sentiment data' },
      { status: 500 }
    );
  }
}
