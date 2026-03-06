# Sentiment Visualization & News Feed Implementation Plan

**Date:** 2026-03-06  
**Status:** Planning  
**Estimated Time:** 4-6 hours total

---

## Overview

Add real-time sentiment analysis visualization and streaming news feed to the QuantShift dashboard.

**Current State:**
- ✅ FinBERT sentiment analysis running in backend
- ✅ Sentiment used for trade filtering
- ❌ No sentiment visualization in dashboard
- ❌ Using mock news data (not real news API)

**Proposed:**
- ✅ Sentiment charts and indicators
- ✅ Real-time news feed with sentiment scores
- ✅ Per-symbol sentiment breakdown
- ✅ Sentiment vs price correlation

---

## Part 1: Sentiment Visualization (2-3 hours)

### Components to Build

#### 1. Sentiment Dashboard Widget
**Location:** `/app/(protected)/dashboard/page.tsx`

**Features:**
- Current overall market sentiment (bullish/bearish/neutral)
- Sentiment gauge (visual indicator)
- Sentiment trend over time (last 24h)
- Top positive/negative symbols

**Visual Design:**
```
┌─────────────────────────────────────┐
│ Market Sentiment                    │
│                                     │
│  ●●●●●○○○○○  Bullish (72%)        │
│                                     │
│  Last 24h: ↗ +15%                  │
│                                     │
│  Top Bullish: WFC (+0.85)          │
│  Top Bearish: EL (-0.42)           │
└─────────────────────────────────────┘
```

#### 2. Sentiment Chart Component
**Location:** `components/dashboard/SentimentChart.tsx`

**Features:**
- Line chart showing sentiment over time
- Color-coded: Green (positive), Red (negative), Gray (neutral)
- Overlay with price movement
- Hover tooltips with news headlines

**Chart Library:** Recharts (already in use)

#### 3. Per-Symbol Sentiment
**Location:** `/app/(protected)/positions/page.tsx`

**Features:**
- Sentiment score next to each position
- Color-coded indicator
- Click to see related news
- Sentiment change (24h)

**Visual:**
```
WFC  $80.54  +2.72%  [●●●●○] +0.65 sentiment
EL   $93.74  -1.97%  [○○●○○] -0.42 sentiment
```

---

## Part 2: Streaming News Feed (2-3 hours)

### News API Integration

#### Option 1: NewsAPI.org (Recommended)
**Pricing:**
- Free: 100 requests/day (sufficient for testing)
- Developer: $449/month (250k requests)

**Implementation:**
```typescript
// app/api/news/route.ts
export async function GET(request: NextRequest) {
  const symbol = request.nextUrl.searchParams.get('symbol');
  
  const response = await fetch(
    `https://newsapi.org/v2/everything?q=${symbol}&apiKey=${process.env.NEWS_API_KEY}`
  );
  
  const articles = await response.json();
  
  // Run through FinBERT for sentiment
  const withSentiment = await analyzeSentiment(articles);
  
  return NextResponse.json(withSentiment);
}
```

#### Option 2: Alpha Vantage (Alternative)
**Pricing:**
- Free: 25 requests/day
- Premium: $49.99/month (unlimited)

**Pros:**
- Includes sentiment scores
- Financial-specific news
- Stock-focused

#### Option 3: Finnhub (Financial Focus)
**Pricing:**
- Free: 60 calls/minute
- Premium: $59.99/month

**Pros:**
- Real-time financial news
- Pre-calculated sentiment
- Good for stocks

### News Feed Component

**Location:** `components/dashboard/NewsFeed.tsx`

**Features:**
- Real-time news stream
- Sentiment indicator per article
- Filter by symbol
- Auto-refresh every 5 minutes
- Click to read full article

**Visual Design:**
```
┌─────────────────────────────────────────┐
│ News Feed                    [Filter ▼] │
├─────────────────────────────────────────┤
│ ● WFC - Wells Fargo beats earnings      │
│   Positive (0.85) • 2 hours ago         │
│                                         │
│ ● EL - Estée Lauder misses revenue     │
│   Negative (-0.42) • 4 hours ago        │
│                                         │
│ ● BTC - Bitcoin ETF inflows surge       │
│   Positive (0.72) • 6 hours ago         │
└─────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend API (1 hour)

**Files to Create:**
- `app/api/sentiment/route.ts` - Get current sentiment scores
- `app/api/news/route.ts` - Fetch news with sentiment
- `app/api/sentiment/history/route.ts` - Historical sentiment data

**Database Schema:**
```sql
-- Add to existing schema
CREATE TABLE sentiment_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    news_count INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sentiment_symbol_time 
ON sentiment_history(symbol, timestamp DESC);
```

### Phase 2: Frontend Components (2 hours)

**Components to Create:**
1. `components/dashboard/SentimentGauge.tsx`
   - Visual gauge showing sentiment
   - Color-coded indicator
   - Percentage display

2. `components/dashboard/SentimentChart.tsx`
   - Time-series chart
   - Sentiment over time
   - Price overlay

3. `components/dashboard/NewsFeed.tsx`
   - Scrollable news list
   - Sentiment indicators
   - Auto-refresh

4. `components/dashboard/SymbolSentiment.tsx`
   - Per-symbol sentiment badge
   - Tooltip with details
   - Click for news

### Phase 3: Integration (1 hour)

**Update Existing Pages:**
- `app/(protected)/dashboard/page.tsx` - Add sentiment widget
- `app/(protected)/positions/page.tsx` - Add sentiment to positions
- `app/(protected)/trades/page.tsx` - Add sentiment to trade history

### Phase 4: News API Setup (30 min)

**Steps:**
1. Sign up for NewsAPI.org (or chosen provider)
2. Add API key to environment variables
3. Configure rate limiting
4. Test API integration
5. Set up caching (Redis)

### Phase 5: Testing (30 min)

**Test Cases:**
- Sentiment scores display correctly
- News feed updates
- Charts render properly
- Mobile responsive
- Error handling (API failures)

---

## Technical Implementation

### API Endpoints

```typescript
// GET /api/sentiment
{
  "overall": {
    "score": 0.65,
    "label": "bullish",
    "confidence": 0.82
  },
  "symbols": [
    {
      "symbol": "WFC",
      "score": 0.85,
      "label": "positive",
      "change_24h": 0.15
    }
  ]
}

// GET /api/news?symbol=WFC&limit=10
{
  "articles": [
    {
      "title": "Wells Fargo beats earnings",
      "source": "Reuters",
      "url": "https://...",
      "published_at": "2026-03-06T10:00:00Z",
      "sentiment": {
        "score": 0.85,
        "label": "positive",
        "confidence": 0.92
      }
    }
  ]
}

// GET /api/sentiment/history?symbol=WFC&days=7
{
  "data": [
    {
      "timestamp": "2026-03-06T00:00:00Z",
      "score": 0.65,
      "label": "positive"
    }
  ]
}
```

### Component Example

```typescript
// components/dashboard/SentimentGauge.tsx
export function SentimentGauge({ symbol }: { symbol: string }) {
  const [sentiment, setSentiment] = useState(null);
  
  useEffect(() => {
    fetch(`/api/sentiment?symbol=${symbol}`)
      .then(res => res.json())
      .then(data => setSentiment(data));
  }, [symbol]);
  
  if (!sentiment) return <div>Loading...</div>;
  
  const color = sentiment.score > 0.5 ? 'green' : 
                sentiment.score < -0.5 ? 'red' : 'gray';
  
  return (
    <div className="sentiment-gauge">
      <div className={`gauge ${color}`}>
        <span>{(sentiment.score * 100).toFixed(0)}%</span>
      </div>
      <div className="label">{sentiment.label}</div>
    </div>
  );
}
```

---

## Cost Analysis

### News API Costs

**NewsAPI.org:**
- Free tier: $0/month (100 requests/day)
- Developer: $449/month (250k requests)
- Business: $1,999/month (unlimited)

**Recommendation:** Start with free tier for testing

**Usage Estimate:**
- 5 symbols × 4 requests/hour × 24 hours = 480 requests/day
- Need Developer tier ($449/month)

**Alternative:** Cache aggressively, reduce update frequency

### Development Cost
- Backend API: 1 hour
- Frontend components: 2 hours
- Integration: 1 hour
- Testing: 30 min
- **Total: 4.5 hours**

---

## Benefits

### For Trading
- ✅ Better signal filtering (already using sentiment)
- ✅ Visual confirmation of sentiment shifts
- ✅ Early warning of negative news
- ✅ Correlation analysis (sentiment vs price)

### For Monitoring
- ✅ Quick sentiment overview
- ✅ Per-position sentiment tracking
- ✅ News feed for context
- ✅ Historical sentiment trends

### For Decision Making
- ✅ See why bot made certain trades
- ✅ Understand position performance
- ✅ Identify sentiment-driven moves
- ✅ Validate strategy effectiveness

---

## Risks & Mitigation

### API Rate Limits
**Risk:** Exceed free tier limits  
**Mitigation:** 
- Cache responses (5-15 min)
- Reduce update frequency
- Upgrade to paid tier if needed

### API Reliability
**Risk:** News API downtime  
**Mitigation:**
- Fallback to cached data
- Graceful degradation
- Multiple API providers

### Sentiment Accuracy
**Risk:** FinBERT misclassifies news  
**Mitigation:**
- Show confidence scores
- Allow manual override
- Track accuracy over time

### Performance
**Risk:** Slow page loads  
**Mitigation:**
- Lazy load components
- Paginate news feed
- Optimize queries

---

## Future Enhancements

### Phase 2 (Later)
- Sentiment alerts (email/SMS)
- Sentiment-based strategy allocation
- News impact analysis
- Sentiment backtesting

### Phase 3 (Advanced)
- Custom news sources
- Social media sentiment (Twitter/Reddit)
- Earnings call transcripts
- SEC filing analysis

---

## Recommendation

**Yes, implement both:**

1. **Sentiment Visualization** (2-3 hours)
   - High value, low effort
   - Leverages existing FinBERT
   - Improves monitoring

2. **Streaming News Feed** (2-3 hours)
   - Provides context for trades
   - Validates sentiment scores
   - Professional appearance

**Total Time:** 4-6 hours  
**Total Cost:** $0 (free tier) or $449/month (paid tier)  
**Value:** High - better insights, improved monitoring, professional dashboard

---

## Next Steps

1. **Approve implementation**
2. **Choose news API provider** (recommend NewsAPI.org)
3. **Sign up for API key**
4. **Build backend APIs** (1 hour)
5. **Build frontend components** (2 hours)
6. **Integrate into dashboard** (1 hour)
7. **Test and deploy** (30 min)

**Can start immediately** - ready to implement when you give the go-ahead.

---

## Questions

1. **News API budget:** Free tier or paid ($449/month)?
2. **Update frequency:** Every 5 min, 15 min, or 1 hour?
3. **Symbols to track:** All positions or just top 10?
4. **Historical data:** How many days of sentiment history?

Let me know your preferences and I'll start building.
