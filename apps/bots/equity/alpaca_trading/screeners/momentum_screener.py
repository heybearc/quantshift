"""Momentum Screener for Crypto and Stocks.

Scans available assets and ranks them by momentum, volume, and trend strength.
Used by trading bots to dynamically select the best opportunities.

Industry Standard Criteria:
- Volume: Minimum $10M daily volume
- Momentum: Price change and RSI-based momentum
- Trend: Above key moving averages
- Volatility: ATR-based volatility filter
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np

import alpaca_trade_api as tradeapi
from alpaca_trading.core.config import config

logger = logging.getLogger(__name__)


@dataclass
class ScreenerResult:
    """Result from screening an asset."""
    symbol: str
    asset_type: str  # "crypto" or "stock"
    current_price: float
    change_24h_pct: float
    volume_24h: float
    rsi: float
    momentum_score: float  # 0-100 composite score
    trend_direction: str  # "up", "down", "sideways"
    volatility: float  # ATR as percentage
    rank: int = 0


class MomentumScreener:
    """Screens crypto and stocks for momentum trading opportunities."""
    
    # Fallback cryptos if dynamic fetch fails
    FALLBACK_CRYPTO = [
        "BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD", "LINK/USD",
        "DOGE/USD", "SHIB/USD", "DOT/USD", "MATIC/USD", "UNI/USD",
        "AAVE/USD", "LTC/USD", "BCH/USD", "XLM/USD", "ATOM/USD",
        "ALGO/USD", "FIL/USD", "NEAR/USD", "APE/USD", "CRV/USD"
    ]
    
    # Stablecoins to exclude from trading (they don't move)
    EXCLUDED_STABLECOINS = ["USDC/USD", "USDT/USD", "DAI/USD", "BUSD/USD", "TUSD/USD", "USDP/USD", "GUSD/USD"]
    
    # High-momentum stocks and ETFs
    STOCK_UNIVERSE = [
        # Leveraged ETFs
        "TQQQ", "SOXL", "TECL", "FNGU", "UPRO", "SPXL",
        # Momentum stocks
        "NVDA", "TSLA", "AMD", "SMCI", "PLTR", "COIN", "MSTR",
        "META", "GOOGL", "AMZN", "MSFT", "AAPL"
    ]
    
    def __init__(self):
        self.api = tradeapi.REST(
            config.api_key,
            config.api_secret,
            config.base_url,
            api_version='v2'
        )
        self._cache = {}
        self._cache_time = None
        self._cache_duration = timedelta(minutes=15)
        self._crypto_universe = None
        self._crypto_universe_time = None
        self._crypto_universe_duration = timedelta(hours=1)  # Refresh available cryptos hourly
    
    def _get_available_cryptos(self) -> List[str]:
        """Dynamically fetch all available crypto trading pairs from Alpaca."""
        # Use cached list if still valid
        if (self._crypto_universe is not None and 
            self._crypto_universe_time is not None and
            datetime.now() - self._crypto_universe_time < self._crypto_universe_duration):
            return self._crypto_universe
        
        try:
            # Get all crypto assets from Alpaca
            assets = self.api.list_assets(asset_class='crypto')
            
            # Filter for tradeable USD pairs
            crypto_symbols = []
            for asset in assets:
                if asset.tradable and asset.status == 'active':
                    # Alpaca returns symbols like "BTC/USD" already formatted
                    symbol = asset.symbol
                    # Only include USD pairs, skip if already has slash or add it
                    if '/USD' in symbol:
                        crypto_symbols.append(symbol)
                    elif symbol.endswith('USD') and '/' not in symbol:
                        # Convert BTCUSD -> BTC/USD
                        base = symbol[:-3]
                        formatted = f"{base}/USD"
                        crypto_symbols.append(formatted)
            
            if crypto_symbols:
                # Filter out stablecoins
                crypto_symbols = [s for s in crypto_symbols if s not in self.EXCLUDED_STABLECOINS]
                self._crypto_universe = crypto_symbols
                self._crypto_universe_time = datetime.now()
                logger.info(f"Loaded {len(crypto_symbols)} tradeable crypto pairs from Alpaca (excluding stablecoins)")
                return crypto_symbols
            else:
                logger.warning("No crypto assets found, using fallback list")
                return self.FALLBACK_CRYPTO
                
        except Exception as e:
            logger.warning(f"Error fetching crypto assets: {e}, using fallback list")
            return self.FALLBACK_CRYPTO
    
    def _get_crypto_bars(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Get historical crypto bars."""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            bars = self.api.get_crypto_bars(
                symbol,
                tradeapi.TimeFrame.Hour,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d")
            ).df
            
            if not bars.empty:
                bars = bars.reset_index()
                if 'symbol' in bars.columns:
                    bars = bars[bars['symbol'] == symbol]
                if not bars.empty:
                    bars = bars.set_index('timestamp')
                    if bars.index.tz is not None:
                        bars.index = bars.index.tz_localize(None)
            
            logger.debug(f"{symbol}: Got {len(bars)} bars")
            return bars
        except Exception as e:
            logger.warning(f"Error getting bars for {symbol}: {e}")
            return pd.DataFrame()
    
    def _get_stock_bars(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Get historical stock bars."""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            bars = self.api.get_bars(
                symbol,
                tradeapi.TimeFrame.Hour,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d")
            ).df
            
            return bars
        except Exception as e:
            logger.debug(f"Error getting stock bars for {symbol}: {e}")
            return pd.DataFrame()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI."""
        if len(prices) < period + 1:
            return 50.0
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _calculate_atr(self, bars: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range as percentage of price."""
        if len(bars) < period + 1:
            return 0.0
        
        high = bars['high']
        low = bars['low']
        close = bars['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        # Return as percentage of current price
        current_price = close.iloc[-1]
        return (atr / current_price * 100) if current_price > 0 else 0.0
    
    def _calculate_momentum_score(
        self, 
        change_24h: float, 
        rsi: float, 
        volume_ratio: float,
        trend_strength: float
    ) -> float:
        """
        Calculate composite momentum score (0-100).
        
        Components:
        - Price momentum (30%): Recent price change
        - RSI position (25%): Favor 40-60 range (not overbought/oversold)
        - Volume (25%): Higher volume = stronger signal
        - Trend (20%): Above moving averages
        """
        # Price momentum score (0-30)
        # Best: 3-10% gain, diminishing returns above
        if change_24h > 0:
            price_score = min(30, change_24h * 3)
        else:
            price_score = max(0, 15 + change_24h)  # Negative change reduces score
        
        # RSI score (0-25)
        # Best: 40-60 range (room to run)
        if 40 <= rsi <= 60:
            rsi_score = 25
        elif 30 <= rsi < 40 or 60 < rsi <= 70:
            rsi_score = 20
        elif 25 <= rsi < 30:
            rsi_score = 22  # Oversold bounce potential
        elif rsi < 25:
            rsi_score = 15  # Too oversold, might keep falling
        else:
            rsi_score = 10  # Overbought
        
        # Volume score (0-25)
        volume_score = min(25, volume_ratio * 10)
        
        # Trend score (0-20)
        trend_score = trend_strength * 20
        
        return price_score + rsi_score + volume_score + trend_score
    
    def _get_trend_direction(self, bars: pd.DataFrame) -> Tuple[str, float]:
        """Determine trend direction and strength."""
        if len(bars) < 20:
            return "sideways", 0.5
        
        close = bars['close']
        current = close.iloc[-1]
        
        # Calculate moving averages
        sma_10 = close.rolling(10).mean().iloc[-1]
        sma_20 = close.rolling(20).mean().iloc[-1]
        
        # Trend direction
        if current > sma_10 > sma_20:
            direction = "up"
            strength = min(1.0, (current - sma_20) / sma_20 * 10 + 0.5)
        elif current < sma_10 < sma_20:
            direction = "down"
            strength = 0.2
        else:
            direction = "sideways"
            strength = 0.5
        
        return direction, strength
    
    def screen_crypto(self, min_volume: float = 10_000) -> List[ScreenerResult]:
        """Screen all cryptos dynamically and return ranked results."""
        results = []
        
        # Get dynamic list of all available cryptos
        crypto_universe = self._get_available_cryptos()
        logger.info(f"Screening {len(crypto_universe)} crypto pairs...")
        
        for symbol in crypto_universe:
            try:
                bars = self._get_crypto_bars(symbol)
                if bars.empty:
                    logger.debug(f"{symbol}: No bars returned")
                    continue
                if len(bars) < 10:
                    logger.debug(f"{symbol}: Only {len(bars)} bars (need 10)")
                    continue
                
                # Get current price and 24h change
                current_price = bars['close'].iloc[-1]
                price_24h_ago = bars['close'].iloc[-24] if len(bars) >= 24 else bars['close'].iloc[0]
                change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                
                # Calculate volume (last 24 hours) - volume is in base currency units
                volume_coins = bars['volume'].iloc[-24:].sum() if len(bars) >= 24 else bars['volume'].sum()
                volume_24h = volume_coins * current_price
                
                # Skip very low volume (lowered threshold significantly)
                if volume_24h < min_volume:
                    logger.debug(f"{symbol}: Low volume ${volume_24h:,.0f}")
                    continue
                
                # Calculate indicators
                rsi = self._calculate_rsi(bars['close'])
                volatility = self._calculate_atr(bars)
                trend_direction, trend_strength = self._get_trend_direction(bars)
                
                # Volume ratio (current vs average)
                avg_volume = bars['volume'].mean()
                recent_volume = bars['volume'].iloc[-6:].mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
                
                # Calculate momentum score
                momentum_score = self._calculate_momentum_score(
                    change_24h, rsi, volume_ratio, trend_strength
                )
                
                results.append(ScreenerResult(
                    symbol=symbol,
                    asset_type="crypto",
                    current_price=current_price,
                    change_24h_pct=change_24h,
                    volume_24h=volume_24h,
                    rsi=rsi,
                    momentum_score=momentum_score,
                    trend_direction=trend_direction,
                    volatility=volatility
                ))
                
            except Exception as e:
                logger.debug(f"Error screening {symbol}: {e}")
                continue
        
        # Sort by momentum score and assign ranks
        results.sort(key=lambda x: x.momentum_score, reverse=True)
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results
    
    def screen_stocks(self, min_volume: float = 5_000_000) -> List[ScreenerResult]:
        """Screen stocks during market hours."""
        # Check if market is open
        clock = self.api.get_clock()
        if not clock.is_open:
            logger.info("Market is closed, skipping stock screening")
            return []
        
        results = []
        
        for symbol in self.STOCK_UNIVERSE:
            try:
                bars = self._get_stock_bars(symbol)
                if bars.empty or len(bars) < 24:
                    continue
                
                current_price = bars['close'].iloc[-1]
                price_24h_ago = bars['close'].iloc[-24] if len(bars) >= 24 else bars['close'].iloc[0]
                change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                
                volume_24h = bars['volume'].iloc[-24:].sum() * current_price if len(bars) >= 24 else 0
                
                if volume_24h < min_volume:
                    continue
                
                rsi = self._calculate_rsi(bars['close'])
                volatility = self._calculate_atr(bars)
                trend_direction, trend_strength = self._get_trend_direction(bars)
                
                avg_volume = bars['volume'].mean()
                recent_volume = bars['volume'].iloc[-6:].mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
                
                momentum_score = self._calculate_momentum_score(
                    change_24h, rsi, volume_ratio, trend_strength
                )
                
                results.append(ScreenerResult(
                    symbol=symbol,
                    asset_type="stock",
                    current_price=current_price,
                    change_24h_pct=change_24h,
                    volume_24h=volume_24h,
                    rsi=rsi,
                    momentum_score=momentum_score,
                    trend_direction=trend_direction,
                    volatility=volatility
                ))
                
            except Exception as e:
                logger.debug(f"Error screening {symbol}: {e}")
                continue
        
        results.sort(key=lambda x: x.momentum_score, reverse=True)
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results
    
    def get_top_opportunities(
        self, 
        top_n: int = 5,
        include_stocks: bool = True,
        min_momentum_score: float = 40.0
    ) -> List[ScreenerResult]:
        """
        Get top trading opportunities across crypto and stocks.
        
        Args:
            top_n: Number of top results to return
            include_stocks: Whether to include stocks (only during market hours)
            min_momentum_score: Minimum score to be considered
        
        Returns:
            List of top opportunities sorted by momentum score
        """
        # Check cache
        if self._cache_time and datetime.now() - self._cache_time < self._cache_duration:
            cached = self._cache.get('top_opportunities', [])
            if cached:
                return cached[:top_n]
        
        all_results = []
        
        # Screen crypto (24/7)
        crypto_results = self.screen_crypto()
        all_results.extend(crypto_results)
        logger.info(f"Screened {len(crypto_results)} cryptos")
        
        # Screen stocks (market hours only)
        if include_stocks:
            stock_results = self.screen_stocks()
            all_results.extend(stock_results)
            logger.info(f"Screened {len(stock_results)} stocks")
        
        # Filter by minimum score
        filtered = [r for r in all_results if r.momentum_score >= min_momentum_score]
        
        # Sort by momentum score
        filtered.sort(key=lambda x: x.momentum_score, reverse=True)
        
        # Re-rank
        for i, result in enumerate(filtered):
            result.rank = i + 1
        
        # Cache results
        self._cache['top_opportunities'] = filtered
        self._cache_time = datetime.now()
        
        return filtered[:top_n]
    
    def get_screener_report(self) -> str:
        """Generate a human-readable screener report."""
        results = self.get_top_opportunities(top_n=10)
        
        if not results:
            return "No opportunities found meeting criteria."
        
        report = ["=" * 60]
        report.append("MOMENTUM SCREENER REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")
        report.append(f"{'Rank':<5} {'Symbol':<12} {'Price':<12} {'24h %':<10} {'RSI':<8} {'Score':<8} {'Trend':<10}")
        report.append("-" * 65)
        
        for r in results:
            report.append(
                f"{r.rank:<5} {r.symbol:<12} ${r.current_price:<10,.2f} "
                f"{r.change_24h_pct:>+7.2f}% {r.rsi:>6.1f} {r.momentum_score:>6.1f} {r.trend_direction:<10}"
            )
        
        report.append("")
        report.append("Criteria: Volume > $1M, Momentum Score > 40")
        
        return "\n".join(report)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    screener = MomentumScreener()
    print(screener.get_screener_report())
