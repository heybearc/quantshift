"""
Sentiment Analyzer - Financial News Sentiment Analysis

Uses FinBERT (pre-trained BERT for financial sentiment) to analyze news articles
and provide sentiment scores for trading symbols. Helps filter bad trades and
boost confidence when sentiment aligns with strategy signals.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

import structlog

logger = structlog.get_logger()


class SentimentAnalyzer:
    """
    Analyze financial news sentiment using FinBERT.
    
    Provides sentiment scores (-1 to +1) for trading symbols based on recent news.
    Can be used to filter signals or adjust position sizes.
    """
    
    def __init__(
        self,
        news_api_key: Optional[str] = None,
        cache_duration_minutes: int = 15,
        use_finbert: bool = True
    ):
        """
        Initialize sentiment analyzer.
        
        Args:
            news_api_key: API key for news service (NewsAPI.org or Alpha Vantage)
            cache_duration_minutes: How long to cache sentiment results
            use_finbert: Use FinBERT model (requires transformers library)
        """
        self.news_api_key = news_api_key
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.use_finbert = use_finbert
        
        # Sentiment cache: {symbol: {timestamp, score, articles}}
        self.sentiment_cache: Dict[str, Dict] = {}
        
        # Initialize FinBERT model if available
        self.model = None
        self.tokenizer = None
        
        if use_finbert:
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch
                
                # Load FinBERT model
                model_name = "ProsusAI/finbert"
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.model.eval()
                
                logger.info("finbert_loaded", model=model_name)
            except ImportError:
                logger.warning(
                    "finbert_unavailable",
                    message="transformers library not installed, using simple sentiment"
                )
                self.use_finbert = False
            except Exception as e:
                logger.error("finbert_load_failed", error=str(e))
                self.use_finbert = False
        
        logger.info(
            "sentiment_analyzer_initialized",
            use_finbert=self.use_finbert,
            cache_duration=cache_duration_minutes
        )
    
    def get_sentiment(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Tuple[float, int, List[Dict]]:
        """
        Get sentiment score for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'SPY', 'AAPL')
            force_refresh: Force fetch new news (ignore cache)
            
        Returns:
            Tuple of (sentiment_score, article_count, articles)
            sentiment_score: -1.0 (very negative) to +1.0 (very positive)
        """
        # Check cache
        if not force_refresh and symbol in self.sentiment_cache:
            cached = self.sentiment_cache[symbol]
            age = datetime.utcnow() - cached['timestamp']
            
            if age < self.cache_duration:
                logger.debug(
                    "sentiment_cache_hit",
                    symbol=symbol,
                    age_minutes=age.total_seconds() / 60
                )
                return cached['score'], cached['count'], cached['articles']
        
        # Fetch and analyze news
        articles = self._fetch_news(symbol)
        
        if not articles:
            logger.debug("no_news_found", symbol=symbol)
            # Return neutral sentiment if no news
            return 0.0, 0, []
        
        # Analyze sentiment
        sentiments = []
        analyzed_articles = []
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            
            if self.use_finbert and self.model:
                sentiment = self._analyze_with_finbert(text)
            else:
                sentiment = self._analyze_simple(text)
            
            sentiments.append(sentiment)
            analyzed_articles.append({
                'title': article.get('title'),
                'source': article.get('source'),
                'published': article.get('publishedAt'),
                'sentiment': sentiment,
                'url': article.get('url')
            })
        
        # Calculate average sentiment
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # Cache result
        self.sentiment_cache[symbol] = {
            'timestamp': datetime.utcnow(),
            'score': avg_sentiment,
            'count': len(articles),
            'articles': analyzed_articles
        }
        
        logger.info(
            "sentiment_analyzed",
            symbol=symbol,
            score=avg_sentiment,
            article_count=len(articles)
        )
        
        return avg_sentiment, len(articles), analyzed_articles
    
    def _fetch_news(self, symbol: str, max_articles: int = 10) -> List[Dict]:
        """
        Fetch recent news for a symbol.
        
        For now, returns mock data. In production, would fetch from:
        - NewsAPI.org
        - Alpha Vantage News API
        - Finnhub
        - Twitter/X API
        """
        # TODO: Implement real news fetching
        # For now, return mock news data
        
        mock_news = [
            {
                'title': f'{symbol} shows strong performance in Q4 earnings',
                'description': 'Company beats analyst expectations with robust revenue growth',
                'source': 'Financial Times',
                'publishedAt': datetime.utcnow().isoformat(),
                'url': 'https://example.com/news1'
            },
            {
                'title': f'Analysts upgrade {symbol} to buy rating',
                'description': 'Multiple analysts raise price targets citing strong fundamentals',
                'source': 'Bloomberg',
                'publishedAt': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'url': 'https://example.com/news2'
            },
            {
                'title': f'{symbol} faces headwinds from regulatory concerns',
                'description': 'New regulations may impact profitability in coming quarters',
                'source': 'Reuters',
                'publishedAt': (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                'url': 'https://example.com/news3'
            }
        ]
        
        return mock_news[:max_articles]
    
    def _analyze_with_finbert(self, text: str) -> float:
        """
        Analyze sentiment using FinBERT model.
        
        Returns:
            Sentiment score: -1.0 (negative) to +1.0 (positive)
        """
        try:
            import torch
            
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT outputs: [positive, negative, neutral]
            # Convert to -1 to +1 scale
            pos_score = predictions[0][0].item()
            neg_score = predictions[0][1].item()
            neutral_score = predictions[0][2].item()
            
            # Calculate weighted sentiment
            sentiment = (pos_score - neg_score)
            
            return sentiment
            
        except Exception as e:
            logger.error("finbert_analysis_failed", error=str(e))
            return 0.0
    
    def _analyze_simple(self, text: str) -> float:
        """
        Simple keyword-based sentiment analysis (fallback).
        
        Returns:
            Sentiment score: -1.0 (negative) to +1.0 (positive)
        """
        text_lower = text.lower()
        
        # Positive keywords
        positive_words = [
            'bullish', 'upgrade', 'beat', 'strong', 'growth', 'profit',
            'gain', 'rise', 'surge', 'rally', 'outperform', 'positive',
            'buy', 'optimistic', 'robust', 'exceed', 'momentum'
        ]
        
        # Negative keywords
        negative_words = [
            'bearish', 'downgrade', 'miss', 'weak', 'decline', 'loss',
            'fall', 'drop', 'plunge', 'sell', 'pessimistic', 'negative',
            'concern', 'risk', 'warning', 'below', 'disappoint'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        # Normalize to -1 to +1
        sentiment = (pos_count - neg_count) / total
        
        return sentiment
    
    def should_filter_signal(
        self,
        symbol: str,
        signal_type: str,
        sentiment_threshold: float = -0.3
    ) -> Tuple[bool, str]:
        """
        Determine if a signal should be filtered based on sentiment.
        
        Args:
            symbol: Trading symbol
            signal_type: 'BUY' or 'SELL'
            sentiment_threshold: Block BUY if sentiment < this value
            
        Returns:
            Tuple of (should_filter, reason)
        """
        sentiment, count, _ = self.get_sentiment(symbol)
        
        # Only filter BUY signals with very negative sentiment
        if signal_type == 'BUY' and sentiment < sentiment_threshold:
            return True, f"Negative sentiment ({sentiment:.2f})"
        
        return False, ""
    
    def get_confidence_boost(
        self,
        symbol: str,
        signal_type: str
    ) -> float:
        """
        Get confidence boost multiplier based on sentiment alignment.
        
        Args:
            symbol: Trading symbol
            signal_type: 'BUY' or 'SELL'
            
        Returns:
            Confidence multiplier (0.5 to 1.5)
            - 1.5 if sentiment strongly aligns with signal
            - 1.0 if neutral
            - 0.5 if sentiment conflicts with signal
        """
        sentiment, count, _ = self.get_sentiment(symbol)
        
        if count == 0:
            return 1.0  # No news, no adjustment
        
        # BUY signal
        if signal_type == 'BUY':
            if sentiment > 0.5:
                return 1.5  # Strong positive sentiment
            elif sentiment > 0.2:
                return 1.2  # Moderate positive
            elif sentiment < -0.3:
                return 0.5  # Negative sentiment
            else:
                return 1.0  # Neutral
        
        # SELL signal
        elif signal_type == 'SELL':
            if sentiment < -0.5:
                return 1.5  # Strong negative sentiment
            elif sentiment < -0.2:
                return 1.2  # Moderate negative
            elif sentiment > 0.3:
                return 0.5  # Positive sentiment (conflicts with sell)
            else:
                return 1.0  # Neutral
        
        return 1.0
    
    def get_sentiment_summary(self) -> Dict[str, Dict]:
        """
        Get summary of all cached sentiments.
        
        Returns:
            Dict of {symbol: {score, count, timestamp}}
        """
        summary = {}
        
        for symbol, data in self.sentiment_cache.items():
            summary[symbol] = {
                'score': data['score'],
                'count': data['count'],
                'timestamp': data['timestamp'].isoformat(),
                'age_minutes': (datetime.utcnow() - data['timestamp']).total_seconds() / 60
            }
        
        return summary
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Clear sentiment cache for a symbol or all symbols."""
        if symbol:
            self.sentiment_cache.pop(symbol, None)
            logger.info("sentiment_cache_cleared", symbol=symbol)
        else:
            self.sentiment_cache.clear()
            logger.info("sentiment_cache_cleared_all")
