# News API Integration for Sentiment Analysis

**Last Updated:** 2026-02-22  
**Status:** 🟡 FinBERT installed, News API pending implementation

---

## Overview

QuantShift uses FinBERT (Financial BERT) for sentiment analysis of news articles to filter trading signals and adjust position sizing. Currently using **mock news data** - this document outlines real news API options for production.

**Current Setup:**
- ✅ FinBERT model installed (ProsusAI/finbert)
- ✅ Sentiment analyzer implemented
- ✅ Signal filtering logic ready
- ⚠️ News fetching: **Mock data only**

---

## Recommended News APIs

### 1. **NewsAPI.org** ⭐ RECOMMENDED

**Best for:** General financial news, easy integration, free tier

**Pricing:**
- **Free:** 100 requests/day, 1-month historical data
- **Developer ($449/month):** 250,000 requests/month, 2-year historical
- **Business ($1,999/month):** Unlimited requests, full historical

**Pros:**
- ✅ Simple REST API
- ✅ Good coverage of financial news sources
- ✅ Free tier sufficient for testing
- ✅ Real-time news updates
- ✅ Filter by source, keyword, date

**Cons:**
- ❌ Free tier limited to 100 requests/day
- ❌ No specialized financial sentiment
- ❌ Rate limits can be restrictive

**Implementation:**
```python
import requests

def fetch_news_newsapi(symbol: str, api_key: str) -> List[Dict]:
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': f'{symbol} stock OR {symbol} earnings',
        'apiKey': api_key,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 10
    }
    response = requests.get(url, params=params)
    return response.json().get('articles', [])
```

**Sign up:** https://newsapi.org/register

---

### 2. **Alpha Vantage News API** ⭐ RECOMMENDED

**Best for:** Stock-specific news, integrated with market data

**Pricing:**
- **Free:** 25 requests/day
- **Premium ($49.99/month):** 75 requests/minute, extended intraday
- **Premium+ ($249.99/month):** 600 requests/minute

**Pros:**
- ✅ Stock-specific news feed
- ✅ Integrated with Alpha Vantage market data
- ✅ Sentiment scores included
- ✅ Ticker-specific filtering
- ✅ Free tier available

**Cons:**
- ❌ Free tier very limited (25/day)
- ❌ Premium pricing adds up

**Implementation:**
```python
def fetch_news_alphavantage(symbol: str, api_key: str) -> List[Dict]:
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'NEWS_SENTIMENT',
        'tickers': symbol,
        'apikey': api_key,
        'limit': 10
    }
    response = requests.get(url, params=params)
    return response.json().get('feed', [])
```

**Sign up:** https://www.alphavantage.co/support/#api-key

---

### 3. **Finnhub** 💰 PREMIUM

**Best for:** Real-time financial news, institutional quality

**Pricing:**
- **Free:** 60 API calls/minute
- **Starter ($59/month):** 300 calls/minute
- **Professional ($99/month):** 600 calls/minute
- **Enterprise:** Custom pricing

**Pros:**
- ✅ High-quality financial news
- ✅ Real-time updates
- ✅ Company-specific news
- ✅ Earnings transcripts
- ✅ SEC filings

**Cons:**
- ❌ No free tier for news API
- ❌ More expensive than alternatives

**Implementation:**
```python
import finnhub

def fetch_news_finnhub(symbol: str, api_key: str) -> List[Dict]:
    finnhub_client = finnhub.Client(api_key=api_key)
    news = finnhub_client.company_news(symbol, _from='2026-02-15', to='2026-02-22')
    return news
```

**Sign up:** https://finnhub.io/register

---

### 4. **Polygon.io** 💰 PREMIUM

**Best for:** Integrated market data + news, crypto support

**Pricing:**
- **Starter ($29/month):** 5 API calls/minute
- **Developer ($99/month):** 100 calls/minute
- **Advanced ($199/month):** Unlimited calls

**Pros:**
- ✅ Integrated with market data API
- ✅ Crypto news support
- ✅ High-quality sources
- ✅ Publisher filtering

**Cons:**
- ❌ No free tier
- ❌ Rate limits on lower tiers

**Implementation:**
```python
from polygon import RESTClient

def fetch_news_polygon(symbol: str, api_key: str) -> List[Dict]:
    client = RESTClient(api_key)
    news = client.list_ticker_news(symbol, limit=10)
    return list(news)
```

**Sign up:** https://polygon.io/

---

### 5. **Twitter/X API** 🐦 SOCIAL SENTIMENT

**Best for:** Social sentiment, real-time market mood

**Pricing:**
- **Free:** Very limited (deprecated)
- **Basic ($100/month):** 10,000 tweets/month
- **Pro ($5,000/month):** 1M tweets/month

**Pros:**
- ✅ Real-time social sentiment
- ✅ Early market signals
- ✅ Trending topics

**Cons:**
- ❌ Expensive for meaningful volume
- ❌ Noisy data (requires filtering)
- ❌ API access restricted

**Implementation:**
```python
import tweepy

def fetch_twitter_sentiment(symbol: str, api_key: str) -> List[Dict]:
    client = tweepy.Client(bearer_token=api_key)
    tweets = client.search_recent_tweets(
        query=f'${symbol} -is:retweet',
        max_results=100
    )
    return tweets.data
```

**Sign up:** https://developer.twitter.com/

---

## Recommended Implementation Strategy

### Phase 1: Start with NewsAPI.org (Free Tier)

**Why:**
- Free 100 requests/day = 10 symbols × 10 requests/day
- Sufficient for testing and validation
- Easy to implement
- No credit card required

**Implementation:**
```python
# In sentiment_analyzer.py
def _fetch_news(self, symbol: str, max_articles: int = 10) -> List[Dict]:
    if not self.news_api_key:
        return self._fetch_mock_news(symbol)  # Fallback to mock
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': f'{symbol} stock OR {symbol} earnings OR {symbol} company',
            'apiKey': self.news_api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': max_articles,
            'from': (datetime.utcnow() - timedelta(days=7)).isoformat()
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        articles = response.json().get('articles', [])
        
        # Convert to standard format
        return [{
            'title': a.get('title'),
            'description': a.get('description'),
            'source': a.get('source', {}).get('name'),
            'publishedAt': a.get('publishedAt'),
            'url': a.get('url')
        } for a in articles]
        
    except Exception as e:
        logger.error("news_fetch_failed", error=str(e))
        return self._fetch_mock_news(symbol)  # Fallback
```

### Phase 2: Upgrade to Alpha Vantage (If needed)

**When to upgrade:**
- Need more than 100 requests/day
- Want stock-specific news filtering
- Need sentiment scores from API

**Cost:** $49.99/month for 75 requests/minute

### Phase 3: Add Twitter/Social Sentiment (Optional)

**For advanced signals:**
- Combine news sentiment + social sentiment
- Weight: 70% news, 30% social
- Detect early market moves

---

## Configuration

### Environment Variables

```bash
# Add to .env file
NEWS_API_KEY=your_newsapi_key_here
NEWS_API_PROVIDER=newsapi  # newsapi, alphavantage, finnhub, polygon

# Optional: Twitter for social sentiment
TWITTER_BEARER_TOKEN=your_twitter_token_here
```

### Bot Configuration

```yaml
# In equity_config.yaml and crypto_config.yaml
orchestrator:
  use_sentiment_analysis: true
  sentiment_config:
    provider: newsapi  # newsapi, alphavantage, finnhub, polygon
    cache_duration_minutes: 15  # Cache news for 15 minutes
    min_articles: 3  # Minimum articles required for sentiment
    sentiment_threshold: -0.3  # Block BUY if sentiment < -0.3
```

---

## Cost Analysis

### For QuantShift (2 bots, 10 symbols total)

**Scenario 1: NewsAPI Free Tier**
- Cost: **$0/month**
- Requests: 100/day
- Usage: Check sentiment every 15 minutes = 96 requests/day
- **Sufficient for current needs** ✅

**Scenario 2: NewsAPI Developer**
- Cost: **$449/month**
- Requests: 250,000/month
- Usage: Unlimited for our scale
- **Overkill for current needs** ❌

**Scenario 3: Alpha Vantage Premium**
- Cost: **$49.99/month**
- Requests: 75/minute
- Usage: More than enough
- **Good middle ground** ✅

**Scenario 4: Finnhub Starter**
- Cost: **$59/month**
- Requests: 300/minute
- Quality: Institutional-grade
- **Best quality/price ratio** ⭐

---

## Implementation Checklist

### Step 1: Sign Up for NewsAPI (Free)
- [ ] Register at https://newsapi.org/register
- [ ] Get API key
- [ ] Add to `.env` file: `NEWS_API_KEY=xxx`

### Step 2: Update Sentiment Analyzer
- [ ] Replace `_fetch_news()` mock data with real API call
- [ ] Add error handling and fallback to mock
- [ ] Test with real news data

### Step 3: Deploy and Test
- [ ] Deploy to primary and standby servers
- [ ] Restart bots
- [ ] Verify news fetching in logs
- [ ] Check sentiment scores are realistic

### Step 4: Monitor Usage
- [ ] Track API request count daily
- [ ] Monitor sentiment accuracy vs price moves
- [ ] Adjust cache duration if hitting rate limits

### Step 5: Evaluate Upgrade (After 30 days)
- [ ] Review sentiment impact on returns
- [ ] Check if free tier is sufficient
- [ ] Upgrade to paid tier if needed

---

## Testing

### Test News Fetching

```bash
# SSH to primary server
ssh quantshift-primary

# Test NewsAPI
cd /opt/quantshift
source venv/bin/activate
python -c "
import requests
api_key = 'YOUR_API_KEY'
response = requests.get('https://newsapi.org/v2/everything', params={
    'q': 'SPY stock',
    'apiKey': api_key,
    'pageSize': 5
})
print(response.json())
"
```

### Test FinBERT Sentiment

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')
model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')

text = 'Apple beats earnings expectations with strong iPhone sales'
inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)

with torch.no_grad():
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
print(f'Positive: {probs[0][0]:.2f}')
print(f'Negative: {probs[0][1]:.2f}')
print(f'Neutral: {probs[0][2]:.2f}')
"
```

---

## Monitoring

### Key Metrics to Track

1. **API Usage:**
   - Requests per day
   - Rate limit hits
   - Failed requests

2. **Sentiment Accuracy:**
   - Sentiment score vs actual price move
   - Correlation over time
   - False positive rate (blocked good trades)

3. **Impact on Returns:**
   - Returns with sentiment filtering vs without
   - Sharpe ratio improvement
   - Drawdown reduction

### Logging

```python
# In sentiment_analyzer.py
logger.info(
    "sentiment_analyzed",
    symbol=symbol,
    score=avg_sentiment,
    article_count=len(articles),
    provider=self.provider,
    cache_hit=cache_hit
)
```

---

## Next Steps

1. **Immediate (This Week):**
   - Sign up for NewsAPI free tier
   - Implement real news fetching
   - Deploy and test

2. **Short-term (This Month):**
   - Monitor sentiment accuracy
   - Validate impact on returns
   - Document findings

3. **Long-term (3-6 Months):**
   - Evaluate paid tier upgrade
   - Consider adding social sentiment
   - Build sentiment accuracy dashboard

---

## References

- **FinBERT Paper:** https://arxiv.org/abs/1908.10063
- **NewsAPI Docs:** https://newsapi.org/docs
- **Alpha Vantage Docs:** https://www.alphavantage.co/documentation/
- **Finnhub Docs:** https://finnhub.io/docs/api
- **Polygon Docs:** https://polygon.io/docs/stocks

---

## Support

**Questions or issues?**
1. Check API provider documentation
2. Review logs: `/opt/quantshift/logs/`
3. Test API key with curl/python
4. Verify rate limits not exceeded
5. Check fallback to mock data is working
