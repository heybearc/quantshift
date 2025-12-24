"""
Alpaca Trading Bot - Core Strategy Implementation

This module implements the Moving Average Crossover strategy for the Alpaca Trading Bot.
It handles real-time trading decisions and order execution with proper risk management.
"""
from typing import Dict, Any, Optional, Tuple
import logging
import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta
import csv
import os

from alpaca_trading.core.config import config
from alpaca_trading.core.exceptions import (
    TradingError, APIConnectionError, APIError, OrderExecutionError,
    InsufficientFundsError, PositionNotFoundError, MarketClosedError, DataError, StrategyError
)
from alpaca_trading.core.notifier import notifier

# Configure logger
logger = logging.getLogger(__name__)

class TradingBot:
    """Main trading bot class implementing the moving average crossover strategy."""
    
    def __init__(self):
        """Initialize the trading bot with Alpaca API client."""
        try:
            self.api = tradeapi.REST(
                config.api_key,
                config.api_secret,
                config.base_url,
                api_version=config.api_version
            )
            # Test the connection
            self.api.get_account()
            logger.info("Successfully connected to Alpaca API")
        except Exception as e:
            error_msg = f"Failed to initialize Alpaca API: {str(e)}"
            logger.critical(error_msg)
            raise APIConnectionError(error_msg) from e
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the current position for a symbol."""
        try:
            position = self.api.get_position(symbol)
            return {
                'symbol': position.symbol,
                'qty': float(position.qty),
                'market_value': float(position.market_value),
                'avg_entry_price': float(position.avg_entry_price),
                'current_price': float(position.current_price),
                'unrealized_pl': float(position.unrealized_pl)
            }
        except Exception as e:
            if 'position does not exist' in str(e).lower():
                return None
            raise OrderExecutionError(f"Error getting position for {symbol}: {str(e)}") from e
    
    def calculate_position_size(self, symbol: str, risk_percent: float = None) -> int:
        """
        Calculate position size based on account equity and ATR-based volatility sizing.
        
        Args:
            symbol: The stock symbol to calculate position size for
            risk_percent: Percentage of account equity to risk (0-1)
            
        Returns:
            int: Number of shares to buy/sell
        """
        if risk_percent is None:
            risk_percent = config.risk_per_trade
        try:
            # Fetch recent daily bars to compute ATR
            bars = self.api.get_bars(symbol, timeframe='1Day', limit=21, adjustment='all', feed='iex')
            if hasattr(bars, 'df'):
                df = bars.df
            else:
                df = pd.DataFrame(bars)

            df = df.sort_index()
            # True Range calculation
            df['tr'] = df[['high', 'low', 'close']].apply(
                lambda row: max(
                    row['high'] - row['low'],
                    abs(row['high'] - row['close']),
                    abs(row['low'] - row['close'])
                ), axis=1)
            atr = df['tr'].rolling(window=14).mean().iloc[-1]

            if pd.isna(atr) or atr == 0:
                raise StrategyError("ATR could not be calculated properly")

            # Calculate position size based on ATR
            account = self.api.get_account()
            equity = float(account.equity)
            risk_amount = equity * risk_percent
            position_size = int(risk_amount / atr)
            return position_size
        except Exception as e:
            error_msg = f"Error calculating position size: {str(e)}"
            logger.error(error_msg)
            raise StrategyError(error_msg) from e
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: Optional[int] = None,
        order_type: str = 'market',
        time_in_force: str = 'gtc'
    ) -> Dict[str, Any]:
        """
        Submit an order to Alpaca.
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            qty: Number of shares (calculated if None based on risk)
            order_type: Type of order ('market', 'limit', etc.)
            time_in_force: Time in force for the order
            
        Returns:
            Dict containing order details
        """
        try:
            # Calculate position size if not provided
            if qty is None:
                qty = self.calculate_position_size(symbol)

            if qty <= 0:
                raise OrderExecutionError(f"Invalid quantity: {qty}")

            # Submit the order
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force
            )

            logger.info(
                "Order submitted - %s %s %s %s @ %s",
                side.upper(),
                qty,
                symbol,
                order_type,
                order.filled_avg_price or 'market'
            )

            # After placing a buy order, submit a trailing stop loss order if supported
            if side == 'buy' and order and hasattr(order, 'id'):
                # Submit trailing stop order (example: 2% trail)
                try:
                    self.api.submit_order(
                        symbol=symbol,
                        qty=qty,
                        side='sell',
                        type='trailing_stop',
                        trail_percent='2',
                        time_in_force='gtc'
                    )
                    logger.info("Trailing stop order placed at 2%% for %s", symbol)
                except Exception as e:  # noqa: BLE001
                    logger.warning("Failed to place trailing stop order: %s", str(e))

                # Submit stop-loss and take-profit using bracket order (if supported)
                try:
                    stop_loss_price = round(float(order.filled_avg_price) * 0.98, 2)  # 2% stop-loss
                    take_profit_price = round(float(order.filled_avg_price) * 1.04, 2)  # 4% take-profit
                    bracket_order = self.api.submit_order(
                        symbol=symbol,
                        qty=qty,
                        side='sell',
                        type='limit',
                        time_in_force='gtc',
                        order_class='bracket',
                        stop_loss={'stop_price': stop_loss_price},
                        take_profit={'limit_price': take_profit_price}
                    )
                    logger.info("Bracket order placed for %s with stop-loss %.2f and take-profit %.2f", symbol, stop_loss_price, take_profit_price)
                except Exception as e:  # noqa: BLE001
                    logger.warning("Failed to place bracket order: %s", str(e))

            # Improved logging: log order details at the end of a successful submit_order
            logger.info("Order ID: %s, Status: %s, Submitted at: %s", order.id, order.status, order.submitted_at)

            return {
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty),
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'status': order.status,
                'side': order.side,
                'type': order.type,
                'time_in_force': order.time_in_force,
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None
            }
        except Exception as e:
            error_msg = f"Error submitting order for {symbol}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise OrderExecutionError(error_msg) from e
    


    

    def log_order_summary(self, order: Dict[str, Any], reason: str) -> None:
        """Record a concise summary of a filled order to CSV and logs.

        Failures in this helper are non-fatal: they are logged and execution continues.
        """
        try:
            msg = (
                f"Trade Executed - {order['side'].upper()} {order['qty']} shares of {order['symbol']}\n"
                f"Price: {order['filled_avg_price']} | Reason: {reason}"
            )
            logger.info(msg)

            path = "trade_history.csv"
            new_file = not os.path.isfile(path)
            with open(path, "a", newline="") as fh:
                fieldnames = [
                    "timestamp",
                    "symbol",
                    "side",
                    "qty",
                    "price",
                    "reason",
                    "order_id",
                ]
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                if new_file:
                    writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": order["submitted_at"],
                        "symbol": order["symbol"],
                        "side": order["side"],
                        "qty": order["qty"],
                        "price": order["filled_avg_price"],
                        "reason": reason,
                        "order_id": order["id"],
                    }
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to persist trade summary: %s", exc)

    def run_strategy(
        self,
        symbol: Optional[str] = None,
        short_window: Optional[int] = None,
        long_window: Optional[int] = None,
        risk_percent: float = 0.01  # Default to 1% risk per trade
    ) -> Dict[str, Any]:
        """
        Execute Moving Average Crossover Strategy
        
        Args:
            symbol: The stock symbol to trade (default: from config)
            short_window: Short moving average window (default: from config)
            long_window: Long moving average window (default: from config)
            risk_percent: Percentage of account equity to risk per trade (0-1)
            
        Returns:
            Dict containing trade signal and execution details
        """
        try:
            # Use config values if parameters are not provided
            symbol = symbol or config.default_symbol
            short_window = short_window or config.short_window
            long_window = long_window or config.long_window
            
            logger.info(f"Running strategy for {symbol} with MA({short_window}, {long_window})")
            
            # Fetch historical data - request more data to ensure we have enough
            days_to_fetch = max(short_window * 2, 90)  # At least 90 days to ensure enough data
            logger.info(f"Fetching up to {days_to_fetch} days of historical data for {symbol} using IEX feed")
            
            # Get the bars using IEX feed which is free
            try:
                bars = self.api.get_bars(
                    symbol,
                    timeframe='1Day',  # Daily bars
                    limit=days_to_fetch,
                    adjustment='all',  # Adjust for splits and dividends
                    feed='iex'  # Use IEX data which is free
                )
                # Convert to DataFrame and ensure we have enough data
                if hasattr(bars, 'df'):
                    bars_df = bars.df
                else:
                    bars_df = pd.DataFrame(bars)
                # If we don't have enough data, try with a larger historical window
                if len(bars_df) < short_window + 1:
                    logger.warning(f"Insufficient recent data points ({len(bars_df)}), trying with older data...")
                    older_bars = self.api.get_bars(
                        symbol,
                        timeframe='1Day',
                        limit=days_to_fetch * 2,  # Try to get more data
                        adjustment='all',
                        feed='iex',
                        start=(datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d'),
                        end=(datetime.utcnow() - timedelta(days=180)).strftime('%Y-%m-%d')
                    )
                    if hasattr(older_bars, 'df'):
                        older_df = older_bars.df
                    else:
                        older_df = pd.DataFrame(older_bars)
                    # Combine with existing data if we have any
                    if not bars_df.empty and not older_df.empty:
                        bars_df = pd.concat([older_df, bars_df])
                    elif not older_df.empty:
                        bars_df = older_df
                logger.info(f"Retrieved {len(bars_df)} bars of data for {symbol}")
                if len(bars_df) < short_window + 1:
                    raise DataError(f"Insufficient data points for {symbol}. Need at least {short_window + 1}, have {len(bars_df)}")
                # Ensure the DataFrame has the expected columns
                if 'close' not in bars_df.columns:
                    raise DataError(f"No 'close' price data available for {symbol}")
                # Sort by date (ascending) and remove duplicates
                bars_df = bars_df.sort_index()
                bars_df = bars_df[~bars_df.index.duplicated(keep='last')]
                # Handle MultiIndex if present (Alpaca v2+)
                if 'symbol' not in bars_df.columns and hasattr(bars_df.index, 'get_level_values'):
                    if 'symbol' in bars_df.index.names:
                        # Filter for our specific symbol if it's in the index
                        bars_df = bars_df.xs(symbol, level='symbol')
                    # Reset index to make sure we have a DatetimeIndex
                    if not isinstance(bars_df.index, pd.DatetimeIndex):
                        bars_df = bars_df.reset_index(drop=False, level='timestamp' if 'timestamp' in bars_df.index.names else None)
                # Ensure we have the required columns
                required_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in required_columns:
                    if col not in bars_df.columns:
                        raise DataError(f"Missing required column in data: {col}")
            except Exception as e:
                error_msg = f"Error fetching data for {symbol}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise DataError(error_msg) from e
            # Validate we have enough data
            if len(bars_df) < short_window + 1:
                raise DataError(f"Insufficient data points for {symbol}. Need at least {short_window + 1}, have {len(bars_df)}")
            
            # Calculate moving averages
            bars_df['short_ma'] = bars_df['close'].rolling(window=short_window, min_periods=1).mean()
            bars_df['long_ma'] = bars_df['close'].rolling(window=long_window, min_periods=1).mean()
            
            # Get valid data points (where both MAs are calculated)
            valid_bars = bars_df.dropna(subset=['short_ma', 'long_ma'])
            
            if len(valid_bars) < 2:
                raise DataError(f"Not enough valid data points after calculating MAs for {symbol}")
            
            # Get the latest two data points for comparison
            latest = valid_bars.iloc[-1]
            prev = valid_bars.iloc[-2]
            
            logger.info(
                f"Latest data - Close: ${latest['close']:.2f}, "
                f"Short MA({short_window}): ${latest['short_ma']:.2f}, "
                f"Long MA({long_window}): ${latest['long_ma']:.2f}"
            )
            
            # Check for crossovers
            golden_cross = (
                prev['short_ma'] < prev['long_ma'] and 
                latest['short_ma'] > latest['long_ma']
            )
            
            death_cross = (
                prev['short_ma'] > prev['long_ma'] and 
                latest['short_ma'] < latest['long_ma']
            )
            # Determine higher timeframe (weekly) trend
            try:
                weekly_bars = self.api.get_bars(
                    symbol,
                    timeframe='1Week',
                    limit=26,
                    adjustment='all',
                    feed='iex'
                )
                if hasattr(weekly_bars, 'df'):
                    weekly_df = weekly_bars.df
                else:
                    weekly_df = pd.DataFrame(weekly_bars)
                if 'close' not in weekly_df.columns or len(weekly_df) < 2:
                    logger.warning("Not enough weekly data for trend confirmation.")
                    weekly_trend_up = True  # Default to true if unclear
                else:
                    weekly_df = weekly_df.sort_index()
                    weekly_df['ma_10'] = weekly_df['close'].rolling(window=10, min_periods=1).mean()
                    weekly_df['ma_20'] = weekly_df['close'].rolling(window=20, min_periods=1).mean()
                    weekly_trend_up = weekly_df.iloc[-1]['ma_10'] > weekly_df.iloc[-1]['ma_20']
                    logger.info(f"Weekly trend for {symbol} is {'UP' if weekly_trend_up else 'DOWN'}")
            except Exception as e:
                weekly_trend_up = True
                logger.warning(f"Error analyzing weekly trend for {symbol}: {str(e)}")
            
            # Get current position
            try:
                position = self.api.get_position(symbol)
                current_position = float(position.qty)
                logger.info(f"Current position in {symbol}: {current_position} shares")
            except Exception as e:
                current_position = 0.0
                logger.info(f"No current position in {symbol}: {str(e)}")

            # Volume confirmation: Check if latest volume is above 20-day average volume
            bars_df['avg_volume_20'] = bars_df['volume'].rolling(window=20).mean()
            latest_avg_vol = bars_df['avg_volume_20'].iloc[-1]
            latest_volume = bars_df['volume'].iloc[-1]
            volume_confirmed = latest_volume > latest_avg_vol
            logger.info(f"Volume confirmation for {symbol}: {'PASSED' if volume_confirmed else 'FAILED'} (latest: {latest_volume}, avg20: {latest_avg_vol})")

            # Identify support and resistance from recent price history
            recent_closes = bars_df['close'].tail(20)
            resistance_level = recent_closes.max()
            support_level = recent_closes.min()

            logger.info(f"Support level: {support_level:.2f}, Resistance level: {resistance_level:.2f}")

            # Calculate stop-loss distance from support for buy signals
            stop_loss_price = support_level
            stop_loss_distance = latest['close'] - stop_loss_price
            if stop_loss_distance <= 0:
                logger.info("Price below support – skip trade decision for now")
                price_clear_of_resistance = False  # force filters to fail so no trade

            # Filter buy signal if close is too close to resistance
            proximity_to_resistance = abs(latest['close'] - resistance_level) / resistance_level
            price_clear_of_resistance = proximity_to_resistance > 0.01  # Allow 1% buffer

            # Generate signals
            signal = 'HOLD'
            signal_reason = 'No crossover detected'

            # Golden cross logic with weekly trend, volume confirmation, and resistance filter
            if golden_cross and weekly_trend_up and volume_confirmed and price_clear_of_resistance:
                signal_reason = 'Golden cross detected (short MA crossed above long MA) with weekly trend up, volume confirmed, and price clear of resistance'
                if current_position <= 0:  # Only buy if we don't already have a position
                    signal = 'BUY'

                    # Calculate position size based on risk and stop-loss distance from support
                    try:
                        account = self.api.get_account()
                        account_equity = float(account.equity)
                        risk_amount = account_equity * risk_percent
                        # Support-based stop-loss sizing
                        position_size = int(risk_amount / stop_loss_distance)
                        # Submit buy order
                        if position_size > 0:
                            order = self.submit_order(
                                symbol=symbol,
                                side='buy',
                                qty=position_size,
                                order_type='market'
                            )
                            # Prepare success response
                            result = {
                                'status': 'success',
                                'action': 'BUY',
                                'symbol': symbol,
                                'qty': position_size,
                                'price': latest['close'],
                                'reason': signal_reason,
                                'order_id': order['id'] if isinstance(order, dict) and 'id' in order else None
                            }
                            # Send notification
                            notifier.send_email(
                                subject=f"Buy Signal - {symbol}",
                                body=(
                                    f"Buy order executed for {symbol}\n"
                                    f"Quantity: {position_size} shares\n"
                                    f"Price: ${latest['close']:.2f}\n"
                                    f"Reason: {signal_reason}"
                                )
                            )
                            self.log_order_summary(order, signal_reason)
                            return result
                    except Exception as e:
                        error_msg = f"Error executing buy order for {symbol}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        raise OrderExecutionError(error_msg) from e
                else:
                    signal_reason = f"Golden cross but already holding {current_position} shares"
            elif golden_cross and not weekly_trend_up:
                signal_reason = "Golden cross detected but weekly trend is not up"
            elif golden_cross and weekly_trend_up and not volume_confirmed:
                signal_reason = "Golden cross and weekly trend up, but volume confirmation failed"
            elif golden_cross and weekly_trend_up and volume_confirmed and not price_clear_of_resistance:
                signal_reason = "Golden cross and weekly trend up and volume confirmed, but price is too close to resistance"
            elif death_cross:
                signal_reason = 'Death cross detected (short MA crossed below long MA)'
                if current_position > 0:  # Only sell if we have a position
                    signal = 'SELL'

                    try:
                        # Submit sell order for all shares
                        order = self.submit_order(
                            symbol=symbol,
                            side='sell',
                            qty=current_position,
                            order_type='market'
                        )
                        # Prepare success response
                        result = {
                            'status': 'success',
                            'action': 'SELL',
                            'symbol': symbol,
                            'qty': current_position,
                            'price': latest['close'],
                            'reason': signal_reason,
                            'order_id': order['id'] if isinstance(order, dict) and 'id' in order else None
                        }
                        # Send notification
                        notifier.send_email(
                            subject=f"Sell Signal - {symbol}",
                            body=(
                                f"Sell order executed for {symbol}\n"
                                f"Quantity: {current_position} shares\n"
                                f"Price: ${latest['close']:.2f}\n"
                                f"Reason: {signal_reason}"
                            )
                        )
                        self.log_order_summary(order, signal_reason)
                        return result
                    except Exception as e:
                        error_msg = f"Error executing sell order for {symbol}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        raise OrderExecutionError(error_msg) from e
                else:
                    signal_reason = 'Death cross but no position to sell'

            # If we get here, no trade was executed
            return {
                'status': 'no_action',
                'symbol': symbol,
                'price': latest['close'],
                'short_ma': latest['short_ma'],
                'long_ma': latest['long_ma'],
                'signal': signal,
                'reason': signal_reason,
                'current_position': current_position,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = f"Error in strategy execution for {symbol}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Try to send error notification
            try:
                notifier.send_email(
                    subject=f"Trading Error - {symbol}",
                    body=f"Error in strategy execution:\n\n{error_msg}\n\n{str(e)}"
                )
            except Exception as notify_err:
                logger.error(f"Failed to send error notification: {str(notify_err)}")
            raise StrategyError(error_msg) from e

# For backward compatibility
def run_strategy(symbol: str = None, short_window: int = None, long_window: int = None) -> Dict[str, Any]:
    """
    Run the trading strategy (legacy function).
    
    This is kept for backward compatibility with existing code.
    """
    bot = TradingBot()
    return bot.run_strategy(symbol, short_window, long_window)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        bot = TradingBot()
        result = bot.run_strategy()
        print(result)
        
        # Import and run performance analysis
        from alpaca_trading.utils.analytics import analyze_performance
        analyze_performance()
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error("Fatal error in main execution", exc_info=True)
# Performance analysis has been moved to utils/analytics.py
# Performance analysis is now handled in utils/analytics.py