# Finnhub API Setup Guide

**Last Updated:** 2026-02-23  
**Status:** Ready for deployment

---

## Overview

Finnhub provides real-time financial news and market data. We use their **free tier** for news sentiment analysis.

**Free Tier Limits:**
- ✅ 60 API calls/minute
- ✅ Company news API access
- ✅ No credit card required
- ✅ Sufficient for 10 symbols (6 calls/min)

---

## Step 1: Get API Key

1. **Sign up:** https://finnhub.io/register
2. **Verify email**
3. **Get API key:** https://finnhub.io/dashboard
4. **Copy the API key** (looks like: `c123abc456def789`)

---

## Step 2: Add to Environment Variables

### On Primary Server

```bash
ssh quantshift-primary

# Edit equity bot service
sudo nano /etc/systemd/system/quantshift-equity.service

# Add this line in the [Service] section after other Environment= lines:
Environment="FINNHUB_API_KEY=YOUR_API_KEY_HERE"

# Edit crypto bot service
sudo nano /etc/systemd/system/quantshift-crypto.service

# Add the same line:
Environment="FINNHUB_API_KEY=YOUR_API_KEY_HERE"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart quantshift-equity quantshift-crypto
```

### On Standby Server

```bash
ssh quantshift-standby

# Edit equity bot service
sudo nano /etc/systemd/system/quantshift-equity.service

# Add this line in the [Service] section:
Environment="FINNHUB_API_KEY=YOUR_API_KEY_HERE"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart quantshift-equity
```

---

## Step 3: Install finnhub-python Library

### On Both Servers

```bash
# Primary
ssh quantshift-primary
cd /opt/quantshift
source venv/bin/activate
pip install finnhub-python
deactivate

# Standby
ssh quantshift-standby
cd /opt/quantshift
source venv/bin/activate
pip install finnhub-python
deactivate
```

---

## Step 4: Verify Integration

### Check Logs

```bash
# On primary server
tail -f /opt/quantshift/logs/equity-bot.log | grep -E 'finnhub|sentiment'
```

**Expected output:**
```
{"event": "finnhub_client_initialized"}
{"event": "finnhub_news_fetched", "symbol": "SPY", "count": 10}
{"event": "sentiment_analyzed", "symbol": "SPY", "score": 0.23, "article_count": 10}
```

**If using mock data (fallback):**
```
{"event": "finnhub_api_key_not_found", "fallback": "mock"}
```

---

## Step 5: Test Sentiment Analysis

### Manual Test

```bash
ssh quantshift-primary
cd /opt/quantshift
source venv/bin/activate

python3 -c "
import os
os.environ['FINNHUB_API_KEY'] = 'YOUR_API_KEY_HERE'

from quantshift_core.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
score, count, articles = analyzer.get_sentiment('AAPL')

print(f'Sentiment Score: {score:.2f}')
print(f'Articles Analyzed: {count}')
print(f'News Provider: {analyzer.news_provider}')
for article in articles[:3]:
    print(f\"  - {article['title']}\")
"
```

**Expected output:**
```
Sentiment Score: 0.15
Articles Analyzed: 10
News Provider: finnhub
  - Apple announces new product line
  - AAPL stock rises on strong earnings
  - Analysts upgrade Apple to buy
```

---

## Configuration Options

### In Bot Config (equity_config.yaml / crypto_config.yaml)

```yaml
orchestrator:
  use_sentiment_analysis: true
  sentiment_config:
    news_provider: 'finnhub'  # or 'mock' for testing
    cache_duration_minutes: 15
    finnhub_api_key: null  # Uses FINNHUB_API_KEY env var if null
```

---

## Rate Limiting

**Free Tier:** 60 requests/minute

**Our Usage:**
- 1 symbol (SPY): ~1 request/minute
- 10 symbols: ~10 requests/minute
- Well under the 60/min limit ✅

**Built-in Protection:**
- 100ms delay between requests
- Automatic fallback to mock data on errors
- 15-minute caching per symbol

---

## Troubleshooting

### Issue: "finnhub_api_key_not_found"

**Solution:**
1. Check environment variable is set: `echo $FINNHUB_API_KEY`
2. Verify systemd service has the variable
3. Restart bot service after adding variable

### Issue: "finnhub_library_not_installed"

**Solution:**
```bash
cd /opt/quantshift
source venv/bin/activate
pip install finnhub-python
systemctl restart quantshift-equity quantshift-crypto
```

### Issue: "finnhub_fetch_failed"

**Possible causes:**
- Invalid API key
- Rate limit exceeded (unlikely with free tier)
- Network connectivity issue
- Symbol not found (use valid ticker symbols)

**Check logs:**
```bash
tail -100 /opt/quantshift/logs/equity-bot-error.log | grep finnhub
```

---

## API Key Security

**✅ Good Practices:**
- Store in environment variables (not in code)
- Use systemd service files (protected by root permissions)
- Never commit API keys to git

**❌ Bad Practices:**
- Hardcoding in Python files
- Storing in config YAML files (tracked by git)
- Sharing API keys publicly

---

## Monitoring

### Check Sentiment Analysis Usage

```bash
# Count sentiment analyses in last hour
grep "sentiment_analyzed" /opt/quantshift/logs/equity-bot.log | \
  grep "$(date -u +%Y-%m-%d)" | wc -l

# Check Finnhub API calls
grep "finnhub_news_fetched" /opt/quantshift/logs/equity-bot.log | \
  tail -20
```

### Monitor Rate Limits

Finnhub free tier is generous (60/min). With our caching (15 min), we'll use:
- **Per symbol:** 4 requests/hour
- **10 symbols:** 40 requests/hour
- **Daily:** ~960 requests/day

**Well within limits!** ✅

---

## Next Steps

After Finnhub is working:

1. ✅ Monitor sentiment scores in logs
2. ✅ Verify signal filtering is working
3. ✅ Track bot performance with sentiment
4. 📋 Consider upgrading to paid tier if needed (unlikely)
5. 📋 Add more symbols to watchlist

---

## Resources

- **Finnhub Dashboard:** https://finnhub.io/dashboard
- **API Documentation:** https://finnhub.io/docs/api
- **Company News API:** https://finnhub.io/docs/api/company-news
- **Support:** support@finnhub.io
