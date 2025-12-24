"""
Golden Cross Stock Scanner
Automatically discovers stocks with golden cross patterns (5MA > 20MA)
"""

import logging
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Set
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

logger = logging.getLogger(__name__)


class GoldenCrossScanner:
    """Scans market for golden cross patterns and manages stock universe"""
    
    def __init__(self, config_path: str = "config/golden_cross_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load scanner configuration"""
        default_config = {
            "scan_universes": [
                "SP500",  # S&P 500
                "NASDAQ100",  # NASDAQ 100
                "DOW30",  # Dow Jones 30
                "RUSSELL1000"  # Russell 1000 (top portion)
            ],
            "min_price": 5.0,
            "max_price": 1000.0,
            "min_volume": 100000,
            "lookback_days": 30,
            "max_stocks_per_universe": 200,
            "golden_cross_age_days": 30,  # How recent the golden cross should be
            "exclude_sectors": ["REIT"],
            "min_market_cap": 100000000,  # $100M minimum
            "max_concurrent_requests": 10
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            logger.info(f"Config file not found, creating default: {self.config_path}")
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def get_universe_symbols(self, universe: str) -> List[str]:
        """Get stock symbols for a given universe"""
        symbols = []
        
        if universe == "SP500":
            symbols = self._get_sp500_symbols()
        elif universe == "NASDAQ100":
            symbols = self._get_nasdaq100_symbols()
        elif universe == "DOW30":
            symbols = self._get_dow30_symbols()
        elif universe == "RUSSELL1000":
            symbols = self._get_russell1000_symbols()
        
        logger.info(f"📊 Retrieved {len(symbols)} symbols from {universe}")
        return symbols[:self.config["max_stocks_per_universe"]]
    
    def _get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            df = tables[0]
            symbols = df['Symbol'].tolist()
            # Clean symbols (remove dots, etc.)
            symbols = [s.replace('.', '-') for s in symbols if isinstance(s, str)]
            return symbols
        except Exception as e:
            logger.error(f"Error fetching S&P 500 symbols: {e}")
            # Fallback to a curated list of major S&P 500 stocks
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B',
                'UNH', 'JNJ', 'JPM', 'V', 'PG', 'XOM', 'HD', 'CVX', 'MA', 'BAC',
                'ABBV', 'PFE', 'AVGO', 'KO', 'LLY', 'MRK', 'TMO', 'COST', 'PEP',
                'WMT', 'ABT', 'ADBE', 'ACN', 'MCD', 'CSCO', 'DHR', 'VZ', 'NEE',
                'BMY', 'TXN', 'LIN', 'PM', 'ORCL', 'WFC', 'CRM', 'DIS', 'AMGN',
                'HON', 'RTX', 'NFLX', 'UPS', 'LOW', 'QCOM', 'T', 'IBM', 'SPGI'
            ]
    
    def _get_nasdaq100_symbols(self) -> List[str]:
        """Get NASDAQ 100 symbols"""
        try:
            url = "https://en.wikipedia.org/wiki/NASDAQ-100"
            tables = pd.read_html(url)
            df = tables[4]  # The main table with companies
            symbols = df['Ticker'].tolist()
            symbols = [s.replace('.', '-') for s in symbols if isinstance(s, str)]
            return symbols
        except Exception as e:
            logger.error(f"Error fetching NASDAQ 100 symbols: {e}")
            # Fallback to major NASDAQ stocks
            return [
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
                'AVGO', 'ORCL', 'COST', 'NFLX', 'ADBE', 'PEP', 'CSCO', 'CMCSA',
                'INTC', 'TXN', 'QCOM', 'AMGN', 'HON', 'INTU', 'AMD', 'SBUX',
                'ISRG', 'BKNG', 'GILD', 'MU', 'ADI', 'LRCX', 'REGN', 'PYPL'
            ]
    
    def _get_dow30_symbols(self) -> List[str]:
        """Get Dow Jones 30 symbols"""
        try:
            url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
            tables = pd.read_html(url)
            df = tables[1]  # The companies table
            symbols = df['Symbol'].tolist()
            symbols = [s.replace('.', '-') for s in symbols if isinstance(s, str)]
            return symbols
        except Exception as e:
            logger.error(f"Error fetching Dow 30 symbols: {e}")
            # Fallback to actual Dow 30 components
            return [
                'AAPL', 'MSFT', 'UNH', 'GS', 'HD', 'MCD', 'CAT', 'V', 'AXP', 'BA',
                'TRV', 'JPM', 'JNJ', 'PG', 'CVX', 'MRK', 'WMT', 'DIS', 'CRM', 'NKE',
                'MMM', 'KO', 'DOW', 'IBM', 'HON', 'AMGN', 'WBA', 'CSCO', 'VZ', 'INTC'
            ]
    
    def _get_russell1000_symbols(self) -> List[str]:
        """Get Russell 1000 symbols (subset via ETF holdings)"""
        try:
            # Use IWB (Russell 1000 ETF) top holdings as proxy
            ticker = yf.Ticker("IWB")
            # This is a simplified approach - in practice you'd use a data provider
            # For now, return a curated list of large caps
            large_caps = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B',
                'UNH', 'JNJ', 'JPM', 'V', 'PG', 'XOM', 'HD', 'CVX', 'MA', 'BAC',
                'ABBV', 'PFE', 'AVGO', 'KO', 'LLY', 'MRK', 'TMO', 'COST', 'PEP',
                'WMT', 'ABT', 'ADBE', 'ACN', 'MCD', 'CSCO', 'DHR', 'VZ', 'NEE',
                'BMY', 'TXN', 'LIN', 'PM', 'ORCL', 'WFC', 'CRM', 'DIS', 'AMGN',
                'HON', 'RTX', 'NFLX', 'UPS', 'LOW', 'QCOM', 'T', 'IBM', 'SPGI'
            ]
            return large_caps
        except Exception as e:
            logger.error(f"Error fetching Russell 1000 symbols: {e}")
            return []
    
    def check_golden_cross(self, symbol: str) -> Dict:
        """Check if a stock has a golden cross pattern"""
        try:
            # Download historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.config["lookback_days"] + 30)
            
            hist = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if hist.empty or len(hist) < 25:  # Need enough data for moving averages
                return {"symbol": symbol, "has_golden_cross": False, "reason": "Insufficient data"}
            
            # Handle multi-level columns if present
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.droplevel(1)
            
            # Calculate moving averages
            hist['MA5'] = hist['Close'].rolling(window=5).mean()
            hist['MA20'] = hist['Close'].rolling(window=20).mean()
            
            # Drop NaN values
            hist = hist.dropna()
            
            # Get recent data
            recent_data = hist.tail(self.config["golden_cross_age_days"])
            
            # Check for golden cross conditions
            if len(hist) < 1:
                return {"symbol": symbol, "has_golden_cross": False, "reason": "No data after processing"}
                
            current_ma5 = hist['MA5'].iloc[-1]
            current_ma20 = hist['MA20'].iloc[-1]
            current_price = hist['Close'].iloc[-1]
            current_volume = hist['Volume'].iloc[-1]
            
            # Validate data
            if pd.isna(current_ma5) or pd.isna(current_ma20) or pd.isna(current_price):
                return {"symbol": symbol, "has_golden_cross": False, "reason": "Invalid moving average data"}
            
            # Basic filters
            if current_price < self.config["min_price"] or current_price > self.config["max_price"]:
                return {"symbol": symbol, "has_golden_cross": False, "reason": f"Price ${current_price:.2f} outside range"}
            
            if pd.isna(current_volume) or current_volume < self.config["min_volume"]:
                return {"symbol": symbol, "has_golden_cross": False, "reason": f"Volume {current_volume:,.0f} too low"}
            
            # Check for golden cross (5MA > 20MA)
            has_golden_cross = bool(current_ma5 > current_ma20)
            
            if not has_golden_cross:
                return {"symbol": symbol, "has_golden_cross": False, "reason": "No golden cross pattern"}
            
            # Check if golden cross is recent (happened within lookback period)
            golden_cross_date = None
            for i in range(len(recent_data) - 1):
                if (recent_data['MA5'].iloc[i] <= recent_data['MA20'].iloc[i] and 
                    recent_data['MA5'].iloc[i + 1] > recent_data['MA20'].iloc[i + 1]):
                    golden_cross_date = recent_data.index[i + 1]
                    break
            
            # Calculate additional metrics
            price_above_ma = (current_price - current_ma5) / current_ma5 * 100
            ma_spread = (current_ma5 - current_ma20) / current_ma20 * 100
            
            # Get company info for additional filtering
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                market_cap = info.get('marketCap', 0)
                sector = info.get('sector', 'Unknown')
                
                if market_cap < self.config["min_market_cap"]:
                    return {"symbol": symbol, "has_golden_cross": False, "reason": f"Market cap ${market_cap:,.0f} too small"}
                
                if sector in self.config["exclude_sectors"]:
                    return {"symbol": symbol, "has_golden_cross": False, "reason": f"Excluded sector: {sector}"}
                
            except:
                market_cap = 0
                sector = "Unknown"
            
            return {
                "symbol": symbol,
                "has_golden_cross": True,
                "golden_cross_date": golden_cross_date.strftime("%Y-%m-%d") if golden_cross_date else "Established",
                "current_price": round(current_price, 2),
                "ma5": round(current_ma5, 2),
                "ma20": round(current_ma20, 2),
                "price_above_ma5": round(price_above_ma, 2),
                "ma_spread": round(ma_spread, 2),
                "volume": int(current_volume),
                "market_cap": market_cap,
                "sector": sector,
                "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error checking golden cross for {symbol}: {e}")
            return {"symbol": symbol, "has_golden_cross": False, "reason": f"Error: {str(e)}"}
    
    def scan_universe(self, universe: str) -> List[Dict]:
        """Scan an entire universe for golden cross stocks"""
        logger.info(f"🔍 Scanning {universe} for golden cross patterns...")
        
        symbols = self.get_universe_symbols(universe)
        if not symbols:
            logger.warning(f"No symbols found for universe: {universe}")
            return []
        
        golden_cross_stocks = []
        
        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=self.config["max_concurrent_requests"]) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self.check_golden_cross, symbol): symbol 
                for symbol in symbols
            }
            
            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_symbol)):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result["has_golden_cross"]:
                        golden_cross_stocks.append(result)
                        logger.info(f"✅ Found golden cross: {symbol} @ ${result['current_price']}")
                    
                    # Progress logging
                    if (i + 1) % 50 == 0:
                        logger.info(f"📊 Processed {i + 1}/{len(symbols)} stocks from {universe}")
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                
                # Rate limiting
                time.sleep(0.1)
        
        logger.info(f"🎯 Found {len(golden_cross_stocks)} golden cross stocks in {universe}")
        return golden_cross_stocks
    
    def scan_all_universes(self) -> List[Dict]:
        """Scan all configured universes for golden cross stocks"""
        logger.info("🚀 Starting comprehensive golden cross scan...")
        
        all_golden_cross_stocks = []
        seen_symbols = set()
        
        for universe in self.config["scan_universes"]:
            logger.info(f"📈 Scanning {universe}...")
            universe_stocks = self.scan_universe(universe)
            
            # Deduplicate across universes
            for stock in universe_stocks:
                if stock["symbol"] not in seen_symbols:
                    stock["discovered_in"] = universe
                    all_golden_cross_stocks.append(stock)
                    seen_symbols.add(stock["symbol"])
        
        # Sort by MA spread (strongest golden crosses first)
        all_golden_cross_stocks.sort(key=lambda x: x.get("ma_spread", 0), reverse=True)
        
        logger.info(f"🏆 Total unique golden cross stocks found: {len(all_golden_cross_stocks)}")
        return all_golden_cross_stocks
    
    def save_golden_cross_stocks(self, stocks: List[Dict], filename: str = "golden_cross_stocks.json") -> None:
        """Save discovered golden cross stocks to file"""
        output_data = {
            "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_stocks": len(stocks),
            "config": self.config,
            "stocks": stocks
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"💾 Saved {len(stocks)} golden cross stocks to {filename}")
    
    def update_manual_stocks_file(self, stocks: List[Dict]) -> None:
        """Update the manual_stocks.json file with discovered golden cross stocks"""
        symbols = [stock["symbol"] for stock in stocks]
        
        # Save to manual_stocks.json (used by dashboard and screener)
        with open("manual_stocks.json", 'w') as f:
            json.dump(symbols, f, indent=2)
        
        logger.info(f"📝 Updated manual_stocks.json with {len(symbols)} golden cross stocks")
        
        # Also save detailed information
        self.save_golden_cross_stocks(stocks, "golden_cross_discovery_details.json")


def main():
    """Main function for standalone execution"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scanner = GoldenCrossScanner()
    
    # Perform comprehensive scan
    golden_cross_stocks = scanner.scan_all_universes()
    
    if golden_cross_stocks:
        # Update the trading bot's stock universe
        scanner.update_manual_stocks_file(golden_cross_stocks)
        
        # Print summary
        print(f"\n🎯 Golden Cross Scan Complete!")
        print(f"📊 Found {len(golden_cross_stocks)} stocks with golden cross patterns")
        print(f"📝 Updated manual_stocks.json for trading bot")
        
        # Show top 10
        print(f"\n🏆 Top 10 Golden Cross Stocks:")
        for i, stock in enumerate(golden_cross_stocks[:10], 1):
            print(f"{i:2d}. {stock['symbol']:6s} - ${stock['current_price']:7.2f} - "
                  f"MA Spread: {stock['ma_spread']:5.1f}% - {stock['sector']}")
    else:
        print("❌ No golden cross stocks found")


if __name__ == "__main__":
    main()
