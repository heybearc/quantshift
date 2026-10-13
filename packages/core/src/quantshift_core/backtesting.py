"""Backtesting framework for strategy validation."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import structlog

logger = structlog.get_logger()


def run_strategy_backtest(strategy, data: pd.DataFrame, initial_capital: float = 100000) -> Optional[Dict]:
    """Walk bars, ask the strategy for signals, and mark the account to market.

    Returns sharpe, total_return, and max_drawdown as fractions, plus the
    number of closed trades. None when the frame has no close column.
    """
    if data is None or len(data) < 2 or "close" not in getattr(data, "columns", []):
        return None

    from .strategies.base_strategy import Account, Position, SignalType

    engine = BacktestEngine(initial_capital=initial_capital, commission=0.0, slippage=0.0)
    symbol = getattr(data, "symbol", None) or "UNKNOWN"
    closed = 0

    for i in range(1, len(data)):
        window = data.iloc[: i + 1]
        price = float(window["close"].iloc[-1])
        if price <= 0:
            continue
        stamp = window.index[i]
        if not isinstance(stamp, datetime):
            stamp = datetime.utcnow()

        if symbol in engine.positions:
            before = len([trade for trade in engine.trades if "pnl" in trade])
            engine.check_stops(symbol, price, stamp)
            closed += len([trade for trade in engine.trades if "pnl" in trade]) - before

        held = engine.positions.get(symbol)
        positions = []
        if held:
            positions.append(Position(
                symbol=symbol,
                quantity=held["quantity"],
                entry_price=held["entry_price"],
                current_price=price,
                market_value=price * held["quantity"],
                unrealized_pl=(price - held["entry_price"]) * held["quantity"],
                unrealized_plpc=(price - held["entry_price"]) / held["entry_price"] if held["entry_price"] else 0,
                side="long",
            ))
        account = Account(
            equity=engine.capital,
            cash=engine.capital,
            buying_power=engine.capital,
            portfolio_value=engine.capital,
            positions_count=len(positions),
        )
        try:
            signals = strategy.generate_signals(window, account, positions) or []
        except Exception as exc:
            logger.warning("backtest_signal_failed", error=str(exc))
            signals = []

        for signal in signals:
            kind = getattr(getattr(signal, "signal_type", None), "value", signal.signal_type)
            kind = str(kind).lower()
            if kind == SignalType.BUY.value and symbol not in engine.positions:
                qty = int(getattr(signal, "position_size", 0) or 0)
                if qty > 0:
                    engine.execute_trade(
                        symbol, "BUY", float(signal.price or price), qty, stamp,
                        getattr(signal, "stop_loss", None),
                        getattr(signal, "take_profit", None),
                    )
            elif kind == SignalType.SELL.value and symbol in engine.positions:
                engine.execute_trade(symbol, "SELL", float(signal.price or price), 0, stamp)
                closed += 1

        engine.update_equity(stamp, {symbol: price})

    if symbol in engine.positions:
        engine.execute_trade(symbol, "SELL", price, 0, stamp)
        closed += 1
        engine.update_equity(stamp, {symbol: price})

    curve = engine.equity_curve
    if len(curve) < 2:
        return None
    returns = pd.Series(curve).pct_change().dropna()
    sharpe = 0.0
    if len(returns) > 1 and returns.std() != 0:
        sharpe = float(returns.mean() / returns.std() * np.sqrt(252))
    peak = curve[0]
    max_dd = 0.0
    for value in curve:
        if value > peak:
            peak = value
        if peak > 0:
            max_dd = max(max_dd, (peak - value) / peak)
    total_return = (curve[-1] - curve[0]) / curve[0] if curve[0] else 0.0
    return {
        "sharpe": sharpe,
        "total_return": float(total_return),
        "max_drawdown": float(max_dd),
        "num_trades": closed,
    }


class BacktestEngine:
    """Backtesting engine for trading strategies."""

    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission: float = 0.0,
        slippage: float = 0.001
    ) -> None:
        """Initialize backtest engine."""
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.reset()

    def reset(self) -> None:
        """Reset backtest state."""
        self.capital = self.initial_capital
        self.positions: Dict[str, Dict] = {}
        self.trades: List[Dict] = []
        self.equity_curve: List[float] = [self.initial_capital]
        self.timestamps: List[datetime] = []

    def execute_trade(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
        timestamp: datetime,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """Execute a trade in the backtest."""
        if action == "BUY":
            cost = price * quantity * (1 + self.slippage) + self.commission
            
            if cost > self.capital:
                logger.warning(
                    "insufficient_capital",
                    symbol=symbol,
                    cost=cost,
                    capital=self.capital
                )
                return False
            
            self.capital -= cost
            self.positions[symbol] = {
                "quantity": quantity,
                "entry_price": price,
                "entry_time": timestamp,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
            
            self.trades.append({
                "symbol": symbol,
                "action": "BUY",
                "price": price,
                "quantity": quantity,
                "timestamp": timestamp,
                "capital": self.capital
            })
            
            logger.debug("trade_executed", action="BUY", symbol=symbol, price=price)
            return True
        
        elif action == "SELL":
            if symbol not in self.positions:
                logger.warning("no_position_to_sell", symbol=symbol)
                return False
            
            position = self.positions[symbol]
            proceeds = price * position["quantity"] * (1 - self.slippage) - self.commission
            self.capital += proceeds
            
            # Calculate P&L
            entry_cost = position["entry_price"] * position["quantity"]
            pnl = proceeds - entry_cost
            pnl_pct = (pnl / entry_cost) * 100
            
            self.trades.append({
                "symbol": symbol,
                "action": "SELL",
                "price": price,
                "quantity": position["quantity"],
                "timestamp": timestamp,
                "capital": self.capital,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "hold_time": (timestamp - position["entry_time"]).total_seconds() / 3600
            })
            
            del self.positions[symbol]
            logger.debug("trade_executed", action="SELL", symbol=symbol, pnl=pnl)
            return True
        
        return False

    def check_stops(self, symbol: str, current_price: float, timestamp: datetime) -> bool:
        """Check if stop loss or take profit hit."""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        
        # Check stop loss
        if position["stop_loss"] and current_price <= position["stop_loss"]:
            logger.info("stop_loss_hit", symbol=symbol, price=current_price)
            self.execute_trade(symbol, "SELL", current_price, position["quantity"], timestamp)
            return True
        
        # Check take profit
        if position["take_profit"] and current_price >= position["take_profit"]:
            logger.info("take_profit_hit", symbol=symbol, price=current_price)
            self.execute_trade(symbol, "SELL", current_price, position["quantity"], timestamp)
            return True
        
        return False

    def update_equity(self, timestamp: datetime, market_prices: Dict[str, float]) -> None:
        """Update equity curve with current market prices."""
        total_equity = self.capital
        
        for symbol, position in self.positions.items():
            if symbol in market_prices:
                market_value = market_prices[symbol] * position["quantity"]
                total_equity += market_value
        
        self.equity_curve.append(total_equity)
        self.timestamps.append(timestamp)

    def get_metrics(self) -> Dict:
        """Calculate backtest performance metrics."""
        if len(self.trades) < 2:
            return {"error": "Not enough trades to calculate metrics"}
        
        # Separate winning and losing trades
        closed_trades = [t for t in self.trades if "pnl" in t]
        if not closed_trades:
            return {"error": "No closed trades"}
        
        winning_trades = [t for t in closed_trades if t["pnl"] > 0]
        losing_trades = [t for t in closed_trades if t["pnl"] <= 0]
        
        # Calculate metrics
        total_trades = len(closed_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t["pnl"] for t in winning_trades)
        total_loss = abs(sum(t["pnl"] for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t["pnl"]) for t in losing_trades]) if losing_trades else 0
        
        # Calculate returns
        final_equity = self.equity_curve[-1]
        total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate max drawdown
        equity_series = pd.Series(self.equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Calculate Sharpe ratio (assuming daily returns)
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 1 else 0
        
        # Calculate average hold time
        avg_hold_time = np.mean([t["hold_time"] for t in closed_trades if "hold_time" in t])
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate * 100,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "total_return": total_return,
            "final_equity": final_equity,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "avg_hold_time_hours": avg_hold_time
        }

    def get_equity_curve_df(self) -> pd.DataFrame:
        """Get equity curve as DataFrame."""
        return pd.DataFrame({
            "timestamp": self.timestamps,
            "equity": self.equity_curve
        })

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as DataFrame."""
        return pd.DataFrame(self.trades)


class WalkForwardOptimizer:
    """Walk-forward optimization to avoid overfitting."""

    def __init__(
        self,
        strategy_class,
        data: pd.DataFrame,
        param_ranges: Dict,
        in_sample_periods: int = 252,
        out_sample_periods: int = 63
    ) -> None:
        """Initialize walk-forward optimizer."""
        self.strategy_class = strategy_class
        self.data = data
        self.param_ranges = param_ranges
        self.in_sample_periods = in_sample_periods
        self.out_sample_periods = out_sample_periods

    def optimize(self) -> Dict:
        """Run walk-forward optimization."""
        results = []
        total_periods = len(self.data)
        
        start_idx = 0
        while start_idx + self.in_sample_periods + self.out_sample_periods <= total_periods:
            # Split data
            in_sample_end = start_idx + self.in_sample_periods
            out_sample_end = in_sample_end + self.out_sample_periods
            
            in_sample_data = self.data.iloc[start_idx:in_sample_end]
            out_sample_data = self.data.iloc[in_sample_end:out_sample_end]
            
            # Optimize on in-sample data
            best_params = self._grid_search(in_sample_data)
            
            # Test on out-of-sample data
            out_sample_metrics = self._backtest_with_params(out_sample_data, best_params)
            
            results.append({
                "window_start": start_idx,
                "best_params": best_params,
                "out_sample_metrics": out_sample_metrics
            })
            
            # Move to next window
            start_idx += self.out_sample_periods
        
        return {
            "windows": results,
            "avg_out_sample_return": np.mean([r["out_sample_metrics"]["total_return"] for r in results]),
            "avg_out_sample_sharpe": np.mean([r["out_sample_metrics"]["sharpe_ratio"] for r in results])
        }

    def _grid_search(self, data: pd.DataFrame) -> Dict:
        """Grid search for best parameters."""
        best_params = {}
        best_sharpe = -float('inf')
        
        # Simple grid search (can be optimized)
        for param_name, param_range in self.param_ranges.items():
            for param_value in param_range:
                params = {param_name: param_value}
                metrics = self._backtest_with_params(data, params)
                
                if metrics["sharpe_ratio"] > best_sharpe:
                    best_sharpe = metrics["sharpe_ratio"]
                    best_params = params
        
        return best_params

    def _backtest_with_params(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Run the strategy on this window and return its metrics."""
        try:
            strategy = self.strategy_class(config=params)
        except TypeError:
            strategy = self.strategy_class(**params)
        result = run_strategy_backtest(strategy, data, 10000)
        if not result:
            return {"sharpe_ratio": 0.0, "total_return": 0.0, "max_drawdown": 0.0, "num_trades": 0}
        return {
            "sharpe_ratio": result["sharpe"],
            "total_return": result["total_return"],
            "max_drawdown": result["max_drawdown"],
            "num_trades": result["num_trades"],
        }
