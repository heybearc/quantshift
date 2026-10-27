"""
Dynamic Symbol Universe Manager

Fetches and ranks symbols dynamically based on:
- Market cap
- Volume
- Volatility
- ML-based tradability scores

This enables QuantShift to scale to 100s of symbols while staying within API limits.
"""

from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout, as_completed
import json
import urllib.request
import structlog
import os

# Liquid Kraken USD pairs. A refresh re-ranks this list by live dollar volume
# and drops any name Kraken no longer lists. Altnames match the bot's orders.
KRAKEN_USD_CANDIDATES = [
    "XBTUSD", "ETHUSD", "SOLUSD", "XRPUSD", "ADAUSD", "AVAXUSD", "DOTUSD",
    "LINKUSD", "LTCUSD", "BCHUSD", "ATOMUSD", "UNIUSD", "AAVEUSD", "NEARUSD",
    "APTUSD", "SUIUSD", "INJUSD", "TIAUSD", "ARBUSD", "OPUSD", "RENDERUSD",
    "FILUSD", "ALGOUSD", "XLMUSD", "HBARUSD", "ICPUSD", "ETCUSD", "XTZUSD",
    "GRTUSD", "IMXUSD", "STXUSD", "SHIBUSD", "PEPEUSD", "WIFUSD", "BONKUSD",
    "SEIUSD", "RUNEUSD", "FETUSD", "POLUSD", "XDGUSD",
]


def refresh_curated_symbols(
    candidates: List[str],
    volumes: Optional[Dict[str, float]],
    max_symbols: int,
    min_volume: float = 0,
    listed: Optional[Set[str]] = None,
) -> List[str]:
    """Keep the curated names that are still listed, best dollar volume first.

    A missing volume does not drop a name. A volume below min_volume does.
    Names absent from `listed` are dropped when that set is provided.
    """
    kept: List[Tuple[float, str]] = []
    for symbol in candidates:
        if listed is not None and symbol not in listed:
            continue
        volume = None if not volumes else volumes.get(symbol)
        if volume is not None and volume < min_volume:
            continue
        kept.append((-1.0 if volume is None else volume, symbol))
    ranked = sorted((item for item in kept if item[0] >= 0), key=lambda item: (-item[0], item[1]))
    unknown = [symbol for volume, symbol in kept if volume < 0]
    ordered = [symbol for _, symbol in ranked] + unknown
    return ordered[:max_symbols]

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
            default_max = 100
        elif executor_type == 'kraken':
            default_max = 25
        else:
            default_max = 50
        self.max_symbols = self.config.get('max_symbols', default_max)
        
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
        elif self.executor_type == 'kraken':
            symbols = self._fetch_kraken_symbols()
        else:
            self.logger.error("unknown_executor_type", executor_type=self.executor_type)
            symbols = None

        if not symbols:
            symbols = self.symbol_cache or self._static_fallback()
            self.logger.warning("symbol_refresh_kept_curated", count=len(symbols))
        
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
        
        The product list has a 5 second deadline. A hang or a timeout
        returns the fixed curated list on purpose.
        """
        candidates = self._get_top_crypto_symbols()
        try:
            listed, volumes = self._coinbase_listing_and_volume(candidates)
        except TimeoutError:
            symbols = self._static_fallback()
            self.logger.warning(
                "coinbase_get_products_using_curated_list",
                count=len(symbols),
                timeout_seconds=5,
            )
            return symbols
        except Exception as exc:
            self.logger.warning("crypto_universe_refresh_failed", error=str(exc))
            return None
        selected = refresh_curated_symbols(
            candidates, volumes, self.max_symbols, self.min_volume, listed
        )
        self.logger.info("crypto_universe_refreshed", selected=len(selected), candidates=len(candidates))
        return selected or None

    def _fetch_kraken_symbols(self) -> Optional[List[str]]:
        """Re-rank the curated Kraken USD list by 24h dollar volume."""
        candidates = list(self.config.get("candidates") or KRAKEN_USD_CANDIDATES)
        try:
            from quantshift_core.executors.kraken_public import kraken_public
            listed, volumes = self._kraken_listing_and_volume(candidates, kraken_public)
        except Exception as exc:
            self.logger.warning("kraken_universe_refresh_failed", error=str(exc))
            return None
        selected = refresh_curated_symbols(
            candidates, volumes, self.max_symbols, self.min_volume, listed
        )
        self.logger.info("kraken_universe_refreshed", selected=len(selected), candidates=len(candidates))
        return selected or None

    def _static_fallback(self) -> List[str]:
        if self.executor_type == "alpaca":
            return self._get_fallback_equity_symbols()[:self.max_symbols]
        if self.executor_type == "kraken":
            candidates = list(self.config.get("candidates") or KRAKEN_USD_CANDIDATES)
            return candidates[:self.max_symbols]
        return self._get_fallback_crypto_symbols()[:self.max_symbols]

    def _kraken_listing_and_volume(self, candidates: List[str], kraken_public) -> Tuple[Set[str], Dict[str, float]]:
        pairs = kraken_public("AssetPairs", {})
        if pairs.get("error"):
            raise RuntimeError(str(pairs.get("error")))
        key_to_alt: Dict[str, str] = {}
        listed: Set[str] = set()
        for key, info in (pairs.get("result") or {}).items():
            if not isinstance(info, dict):
                continue
            alt = info.get("altname")
            if not alt:
                continue
            key_to_alt[key] = alt
            if info.get("status") in (None, "online"):
                listed.add(alt)
        ticker = kraken_public("Ticker", {"pair": ",".join(candidates)})
        if ticker.get("error"):
            raise RuntimeError(str(ticker.get("error")))
        volumes: Dict[str, float] = {}
        for key, info in (ticker.get("result") or {}).items():
            alt = key_to_alt.get(key)
            if not alt or not isinstance(info, dict):
                continue
            try:
                last = float(info["c"][0])
                day_volume = float(info["v"][1])
            except (KeyError, TypeError, ValueError, IndexError):
                continue
            volumes[alt] = last * day_volume
        return listed, volumes

    def _read_json(self, url: str, timeout: float):
        request = urllib.request.Request(url, headers={"User-Agent": "quantshift"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())

    def _read_json_deadline(self, url: str, timeout: float):
        """Stop waiting even when the socket timeout does not fire."""
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(self._read_json, url, timeout)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeout as exc:
            raise TimeoutError(f"timed out after {timeout}s: {url}") from exc
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

    def _coinbase_listing_and_volume(self, candidates: List[str]) -> Tuple[Optional[Set[str]], Dict[str, float]]:
        """Listed USD products, plus dollar volume for the curated names. Times out."""
        try:
            products = self._read_json_deadline("https://api.exchange.coinbase.com/products", 5)
        except TimeoutError:
            self.logger.warning("coinbase_get_products_timeout", timeout_seconds=5, fallback="curated_list")
            raise
        listed = {
            item.get("id")
            for item in products
            if isinstance(item, dict)
            and item.get("status") == "online"
            and not item.get("trading_disabled")
            and str(item.get("id", "")).endswith("-USD")
        }
        volumes: Dict[str, float] = {}

        def one(symbol: str) -> Tuple[str, Optional[float]]:
            try:
                stats = self._read_json(
                    f"https://api.exchange.coinbase.com/products/{symbol}/stats",
                    2,
                )
                return symbol, float(stats["volume"]) * float(stats["last"])
            except Exception:
                return symbol, None

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(one, symbol) for symbol in candidates if symbol in listed]
            try:
                for future in as_completed(futures, timeout=12):
                    try:
                        symbol, volume = future.result()
                    except Exception:
                        continue
                    if volume is not None:
                        volumes[symbol] = volume
            except FuturesTimeout:
                self.logger.warning("coinbase_product_stats_timeout", collected=len(volumes))
        return listed, volumes
    
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
        # Top 50 cryptos verified on Coinbase (October 2026)
        # Removed: USDT, USDC (stablecoins), BNB (not on Coinbase),
        # MATIC, ENJ, GALA, FTM, TRX, MKR, EOS, RNDR, LRC (delisted)
        return [
            'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD',
            'AVAX-USD', 'DOT-USD', 'DOGE-USD', 'LINK-USD', 'UNI-USD',
            'ATOM-USD', 'LTC-USD', 'XLM-USD', 'ALGO-USD', 'BCH-USD',
            'FIL-USD', 'AAVE-USD', 'SUI-USD', 'COMP-USD', 'SNX-USD',
            'YFI-USD', 'SUSHI-USD', 'CRV-USD', 'BAL-USD', 'ZRX-USD',
            'MANA-USD', 'SAND-USD', 'AXS-USD', 'SHIB-USD', 'CHZ-USD',
            'BAT-USD', 'ZEC-USD', 'DASH-USD', 'ETC-USD', 'XTZ-USD',
            'APT-USD', 'NEAR-USD', 'HBAR-USD', 'ICP-USD', 'APE-USD',
            'LDO-USD', 'ARB-USD', 'OP-USD', 'IMX-USD', 'RENDER-USD',
            'INJ-USD', 'STX-USD', 'GRT-USD', 'TIA-USD', 'SKL-USD'
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
        
        # Top 50 cryptos by market cap (verified on Coinbase as of October 2026)
        # Removed delisted/invalid symbols: MATIC, ENJ, GALA, FTM, TRX, MKR, EOS, RNDR, LRC
        top_50 = [
            'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD',
            'AVAX-USD', 'DOT-USD', 'DOGE-USD', 'LINK-USD', 'UNI-USD',
            'ATOM-USD', 'LTC-USD', 'XLM-USD', 'ALGO-USD', 'BCH-USD',
            'FIL-USD', 'AAVE-USD', 'SUI-USD', 'COMP-USD', 'SNX-USD',
            'YFI-USD', 'SUSHI-USD', 'CRV-USD', 'BAL-USD', 'ZRX-USD',
            'MANA-USD', 'SAND-USD', 'AXS-USD', 'SHIB-USD', 'CHZ-USD',
            'BAT-USD', 'ZEC-USD', 'DASH-USD', 'ETC-USD', 'XTZ-USD',
            'APT-USD', 'NEAR-USD', 'HBAR-USD', 'ICP-USD', 'APE-USD',
            'LDO-USD', 'ARB-USD', 'OP-USD', 'IMX-USD', 'RENDER-USD',
            'INJ-USD', 'STX-USD', 'GRT-USD', 'TIA-USD', 'SKL-USD'
        ]
        
        return top_50[:self.max_symbols]
