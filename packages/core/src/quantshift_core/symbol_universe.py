"""
Dynamic Symbol Universe Manager

Fetches and ranks symbols dynamically based on:
- Market cap
- Volume
- Volatility
- ML-based tradability scores

This enables QuantShift to scale to 100s of symbols while staying within API limits.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import structlog
import os

logger = structlog.get_logger()


class SymbolUniverse:
    """
    Manages dynamic symbol selection for trading bots.
    
    Phase 1: Fetch top N symbols by volume/market cap
    Phase 2: ML-based ranking and filtering
    Phase 3: Per-symbol strategy recommendation
    """
    
    def __init__(self, executor_type: str, config: Optional[Dict] = None, api_client=None):
        """
        Initialize symbol universe manager.
        
        Args:
            executor_type: 'alpaca' or 'coinbase'
            config: Configuration dict with optional keys:
                - max_symbols: Maximum symbols to return (default: 100 for equity, 50 for crypto)
                - min_volume: Minimum daily volume filter
                - exclude_symbols: List of symbols to exclude
            api_client: Optional API client (Alpaca TradingClient or Coinbase RESTClient)
                       If provided, enables real-time symbol fetching
        """
        self.executor_type = executor_type
        self.config = config or {}
        self.api_client = api_client
        self.logger = logger.bind(executor_type=executor_type)
        
        # Default limits based on executor type
        if executor_type == 'alpaca':
            self.max_symbols = self.config.get('max_symbols', 100)
        else:  # coinbase
            self.max_symbols = self.config.get('max_symbols', 50)
        
        self.min_volume = self.config.get('min_volume', 1_000_000)
        self.exclude_symbols = set(self.config.get('exclude_symbols', []))
        
        # Cache
        self.symbol_cache = None
        self.cache_timestamp = None
        self.cache_duration = timedelta(hours=24)  # Refresh daily
        
        self.logger.info(
            "symbol_universe_initialized",
            max_symbols=self.max_symbols,
            min_volume=self.min_volume,
            has_api_client=api_client is not None
        )
    
    def get_symbols(self, force_refresh: bool = False) -> List[str]:
        """
        Get list of symbols to trade.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            List of symbol strings
        """
        # Check cache
        if not force_refresh and self._is_cache_valid():
            self.logger.debug("symbol_cache_hit", count=len(self.symbol_cache))
            return self.symbol_cache
        
        # Fetch fresh symbols
        self.logger.info("fetching_symbols", executor_type=self.executor_type)
        
        if self.executor_type == 'alpaca':
            symbols = self._fetch_alpaca_symbols()
        elif self.executor_type == 'coinbase':
            symbols = self._fetch_coinbase_symbols()
        else:
            self.logger.error("unknown_executor_type", executor_type=self.executor_type)
            return []
        
        # Update cache
        self.symbol_cache = symbols
        self.cache_timestamp = datetime.utcnow()
        
        self.logger.info(
            "symbols_fetched",
            count=len(symbols),
            executor_type=self.executor_type
        )
        
        return symbols
    
    def _is_cache_valid(self) -> bool:
        """Check if symbol cache is still valid."""
        if self.symbol_cache is None or self.cache_timestamp is None:
            return False
        
        age = datetime.utcnow() - self.cache_timestamp
        return age < self.cache_duration
    
    def _fetch_alpaca_symbols(self) -> List[str]:
        """
        Fetch top equity symbols from Alpaca.
        
        Strategy:
        1. Get all active, tradable assets
        2. Filter by volume and tradability
        3. Return top N by volume
        """
        try:
            from alpaca.trading.requests import GetAssetsRequest
            from alpaca.trading.enums import AssetClass, AssetStatus
            
            # Use passed client if available, otherwise create new one
            if self.api_client:
                client = self.api_client
            else:
                from alpaca.trading.client import TradingClient
                api_key = os.getenv('APCA_API_KEY_ID')
                api_secret = os.getenv('APCA_API_SECRET_KEY')
                
                if not api_key or not api_secret:
                    self.logger.error("alpaca_credentials_missing")
                    return self._get_fallback_equity_symbols()
                
                client = TradingClient(api_key, api_secret, paper=True)
            
            # Get all US equity assets
            search_params = GetAssetsRequest(
                status=AssetStatus.ACTIVE,
                asset_class=AssetClass.US_EQUITY
            )
            
            assets = client.get_all_assets(search_params)
            
            # Filter and rank by tradability
            tradable_symbols = []
            
            for asset in assets:
                # Must be tradable and not in exclude list
                if (asset.tradable and 
                    asset.fractionable and 
                    asset.shortable and
                    asset.symbol not in self.exclude_symbols):
                    tradable_symbols.append(asset.symbol)
            
            # For now, use predefined list of top 100 by market cap
            # In Phase 2, we'll add real-time volume/market cap ranking
            top_symbols = self._get_sp100_symbols()
            
            # Filter to only include tradable symbols
            result = [s for s in top_symbols if s in tradable_symbols][:self.max_symbols]
            
            self.logger.info(
                "alpaca_symbols_fetched",
                total_assets=len(assets),
                tradable=len(tradable_symbols),
                selected=len(result)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "alpaca_fetch_failed",
                error=str(e)
            )
            return self._get_fallback_equity_symbols()
    
    def _fetch_coinbase_symbols(self) -> List[str]:
        """
        Fetch top crypto symbols from Coinbase.
        
        NOTE: Coinbase get_products() API is unreliable and causes hangs.
        Using curated fallback list for Phase 1. Will implement proper
        API-based fetching in Phase 2 with better error handling.
        """
        self.logger.info(
            "using_curated_crypto_list",
            reason="coinbase_api_unreliable",
            count=self.max_symbols
        )
        return self._get_fallback_crypto_symbols()
    
    def _get_sp100_symbols(self) -> List[str]:
        """
        Get S&P 100 symbols (top 100 large-cap US stocks).
        
        This is a curated list of highly liquid, high market cap stocks.
        Phase 2 will replace this with dynamic ranking.
        """
        return [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ORCL',
            'ADBE', 'CRM', 'CSCO', 'ACN', 'AMD', 'INTC', 'IBM', 'QCOM', 'TXN', 'INTU',
            
            # Financial
            'BRK.B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'SPGI', 'BLK',
            'C', 'AXP', 'SCHW', 'CB', 'PGR', 'MMC', 'ICE', 'CME', 'AON', 'TFC',
            
            # Healthcare
            'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'PFE', 'BMY',
            'AMGN', 'GILD', 'CVS', 'CI', 'ELV', 'HUM', 'ISRG', 'VRTX', 'REGN', 'ZTS',
            
            # Consumer
            'WMT', 'HD', 'PG', 'KO', 'PEP', 'COST', 'MCD', 'NKE', 'SBUX', 'TGT',
            'LOW', 'TJX', 'EL', 'MDLZ', 'CL', 'KMB', 'GIS', 'HSY', 'CLX', 'SJM',
            
            # Communication
            'DIS', 'CMCSA', 'NFLX', 'T', 'VZ', 'TMUS', 'CHTR', 'EA', 'ATVI', 'TTWO',
            
            # Industrials
            'UPS', 'HON', 'UNP', 'RTX', 'CAT', 'BA', 'GE', 'MMM', 'DE', 'LMT',
            
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL',
            
            # ETFs (high volume, broad market)
            'SPY', 'QQQ', 'IWM', 'DIA', 'VOO', 'VTI', 'IVV', 'EEM', 'GLD', 'SLV'
        ]
    
    def _get_top_crypto_symbols(self) -> List[str]:
        """
        Get top 50 crypto symbols by market cap.
        
        This is a curated list of top cryptocurrencies.
        Phase 2 will replace this with dynamic ranking.
        """
        return [
            # Top 10 by market cap
            'BTC-USD', 'ETH-USD', 'USDT-USD', 'BNB-USD', 'SOL-USD',
            'XRP-USD', 'USDC-USD', 'ADA-USD', 'AVAX-USD', 'DOGE-USD',
            
            # Top 11-30
            'TRX-USD', 'DOT-USD', 'MATIC-USD', 'LTC-USD', 'SHIB-USD',
            'BCH-USD', 'LINK-USD', 'UNI-USD', 'ATOM-USD', 'XLM-USD',
            'ETC-USD', 'FIL-USD', 'HBAR-USD', 'APT-USD', 'ARB-USD',
            'VET-USD', 'ALGO-USD', 'NEAR-USD', 'GRT-USD', 'SAND-USD',
            
            # Top 31-50 (high volume, good liquidity)
            'MANA-USD', 'AAVE-USD', 'MKR-USD', 'SNX-USD', 'COMP-USD',
            'SUSHI-USD', 'YFI-USD', 'CRV-USD', 'BAL-USD', 'REN-USD',
            'ZRX-USD', 'ENJ-USD', 'BAT-USD', 'LRC-USD', 'OMG-USD',
            'SKL-USD', 'STORJ-USD', 'AMP-USD', 'ANKR-USD', 'NKN-USD'
        ]
    
    def _get_fallback_equity_symbols(self) -> List[str]:
        """Fallback to minimal symbol set if API fails."""
        self.logger.warning("using_fallback_equity_symbols")
        return ['SPY', 'QQQ', 'IWM', 'DIA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA']
    
    def _get_fallback_crypto_symbols(self) -> List[str]:
        """
        Fallback to curated top-50 crypto symbols by market cap.
        Used when Coinbase API is unreliable.
        """
        self.logger.warning("using_fallback_crypto_symbols")
        
        # Top 50 cryptos by market cap (as of 2026)
        top_50 = [
            'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
            'ADA-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD', 'LINK-USD',
            'UNI-USD', 'ATOM-USD', 'LTC-USD', 'XLM-USD', 'ALGO-USD',
            'VET-USD', 'FIL-USD', 'AAVE-USD', 'MKR-USD', 'COMP-USD',
            'SNX-USD', 'YFI-USD', 'SUSHI-USD', 'CRV-USD', 'BAL-USD',
            'ZRX-USD', 'ENJ-USD', 'MANA-USD', 'SAND-USD', 'AXS-USD',
            'GALA-USD', 'CHZ-USD', 'BAT-USD', 'ZEC-USD', 'DASH-USD',
            'ETC-USD', 'XTZ-USD', 'EOS-USD', 'NEAR-USD', 'FTM-USD',
            'HBAR-USD', 'ICP-USD', 'APE-USD', 'LDO-USD', 'ARB-USD',
            'OP-USD', 'IMX-USD', 'RNDR-USD', 'INJ-USD', 'STX-USD'
        ]
        
        return top_50[:self.max_symbols]
