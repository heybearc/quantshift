#!/usr/bin/env python3
"""
QuantShift Equity Bot Backtest
Mirrors the exact live bot logic: MA 5/20 crossover + RSI filter + ATR-based SL/TP
Uses Alpaca free historical data (no Yahoo Finance dependency).

Usage:
    python run_backtest.py
    python run_backtest.py --symbols SPY QQQ AAPL --years 3
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Config — mirrors equity_strategy.yaml
# ---------------------------------------------------------------------------
DEFAULT_SYMBOLS   = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL"]
SHORT_WINDOW      = 5
LONG_WINDOW       = 20
RSI_PERIOD        = 14
ATR_PERIOD        = 14
ATR_SL_MULT       = 2.0    # stop loss = entry - (ATR * 2)
ATR_TP_MULT       = 4.0    # take profit = entry + (ATR * 4)  [2:1 RR]
RISK_PCT          = 0.01   # 1% of equity risked per trade
MAX_POSITIONS     = 5
STARTING_CAPITAL  = 100_000.0


# ---------------------------------------------------------------------------
# Indicators (pure pandas — no external deps beyond numpy)
# ---------------------------------------------------------------------------

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sma_fast"] = sma(df["close"], SHORT_WINDOW)
    df["sma_slow"] = sma(df["close"], LONG_WINDOW)
    df["rsi"]      = rsi(df["close"], RSI_PERIOD)
    df["atr"]      = atr(df["high"], df["low"], df["close"], ATR_PERIOD)
    return df


# ---------------------------------------------------------------------------
# Data fetch — Yahoo Finance (free, no API key)
# ---------------------------------------------------------------------------

def fetch_bars(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    """Fetch daily OHLCV bars from Yahoo Finance."""
    try:
        import yfinance as yf
    except ImportError:
        print("ERROR: yfinance not installed. Run: pip install yfinance")
        sys.exit(1)

    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, interval="1d", auto_adjust=True)
    
    if df.empty:
        raise ValueError(f"No data returned for {symbol}")
    
    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume",
    })
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df[["open", "high", "low", "close", "volume"]].sort_index()
    return df


# ---------------------------------------------------------------------------
# Signal generation — mirrors MACrossoverStrategy in live bot
# ---------------------------------------------------------------------------

def generate_signal(row: pd.Series, prev: pd.Series) -> Optional[str]:
    """Returns 'BUY', 'SELL', or None. Mirrors live bot logic exactly."""
    if pd.isna(row["sma_fast"]) or pd.isna(row["sma_slow"]) or pd.isna(row["rsi"]):
        return None

    # Golden cross — fast crosses above slow, RSI not overbought
    if row["sma_fast"] > row["sma_slow"] and prev["sma_fast"] <= prev["sma_slow"]:
        if row["rsi"] < 70:
            return "BUY"

    # Death cross — fast crosses below slow, RSI not oversold
    elif row["sma_fast"] < row["sma_slow"] and prev["sma_fast"] >= prev["sma_slow"]:
        if row["rsi"] > 30:
            return "SELL"

    return None


# ---------------------------------------------------------------------------
# Position sizing — mirrors live bot ATR logic
# ---------------------------------------------------------------------------

def calc_position_size(equity: float, price: float, atr_val: float) -> Tuple[int, float, float]:
    """Returns (shares, stop_loss, take_profit)."""
    stop_distance = atr_val * ATR_SL_MULT
    risk_dollars   = equity * RISK_PCT
    shares = int(risk_dollars / stop_distance) if stop_distance > 0 else 0
    shares = max(shares, 1)

    # Cap at 20% of equity per position
    max_shares = int((equity * 0.20) / price)
    shares = min(shares, max_shares)

    stop_loss   = price - stop_distance
    take_profit = price + (atr_val * ATR_TP_MULT)
    return shares, stop_loss, take_profit


# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------

def backtest_symbol(symbol: str, df: pd.DataFrame) -> Dict:
    """Run backtest for a single symbol. Returns trade log and metrics."""
    df = add_indicators(df)
    df = df.dropna(subset=["sma_fast", "sma_slow", "rsi", "atr"])

    equity    = STARTING_CAPITAL
    position  = None   # {shares, entry_price, stop_loss, take_profit, entry_date}
    trades    = []
    equity_curve = []

    rows = list(df.iterrows())
    for i in range(1, len(rows)):
        date, row = rows[i]
        _, prev   = rows[i - 1]
        price     = row["close"]

        # Check SL/TP on open position
        if position:
            hit_sl = price <= position["stop_loss"]
            hit_tp = price >= position["take_profit"]
            if hit_sl or hit_tp:
                exit_price  = position["stop_loss"] if hit_sl else position["take_profit"]
                pnl         = (exit_price - position["entry_price"]) * position["shares"]
                equity     += pnl
                trades.append({
                    "symbol":      symbol,
                    "entry_date":  position["entry_date"],
                    "exit_date":   date,
                    "entry_price": position["entry_price"],
                    "exit_price":  exit_price,
                    "shares":      position["shares"],
                    "pnl":         pnl,
                    "pnl_pct":     pnl / (position["entry_price"] * position["shares"]) * 100,
                    "exit_reason": "stop_loss" if hit_sl else "take_profit",
                })
                position = None

        sig = generate_signal(row, prev)

        if sig == "BUY" and position is None:
            atr_val = row["atr"]
            shares, sl, tp = calc_position_size(equity, price, atr_val)
            cost = shares * price
            if cost <= equity * 0.95:   # keep 5% cash buffer
                position = {
                    "shares":      shares,
                    "entry_price": price,
                    "stop_loss":   sl,
                    "take_profit": tp,
                    "entry_date":  date,
                }

        elif sig == "SELL" and position:
            pnl    = (price - position["entry_price"]) * position["shares"]
            equity += pnl
            trades.append({
                "symbol":      symbol,
                "entry_date":  position["entry_date"],
                "exit_date":   date,
                "entry_price": position["entry_price"],
                "exit_price":  price,
                "shares":      position["shares"],
                "pnl":         pnl,
                "pnl_pct":     pnl / (position["entry_price"] * position["shares"]) * 100,
                "exit_reason": "sell_signal",
            })
            position = None

        equity_curve.append({"date": date, "equity": equity})

    # Close any open position at last price
    if position:
        last_price = df.iloc[-1]["close"]
        pnl = (last_price - position["entry_price"]) * position["shares"]
        equity += pnl
        trades.append({
            "symbol":      symbol,
            "entry_date":  position["entry_date"],
            "exit_date":   df.index[-1],
            "entry_price": position["entry_price"],
            "exit_price":  last_price,
            "shares":      position["shares"],
            "pnl":         pnl,
            "pnl_pct":     pnl / (position["entry_price"] * position["shares"]) * 100,
            "exit_reason": "end_of_data",
        })

    return {
        "symbol":       symbol,
        "trades":       trades,
        "final_equity": equity,
        "equity_curve": equity_curve,
    }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def calc_metrics(results: List[Dict], start: datetime, end: datetime) -> Dict:
    all_trades = []
    for r in results:
        all_trades.extend(r["trades"])

    if not all_trades:
        return {"error": "No trades generated"}

    df = pd.DataFrame(all_trades)
    closed = df[df["exit_reason"] != "end_of_data"]

    wins   = closed[closed["pnl"] > 0]
    losses = closed[closed["pnl"] <= 0]

    win_rate      = len(wins) / len(closed) * 100 if len(closed) else 0
    avg_win       = wins["pnl"].mean() if len(wins) else 0
    avg_loss      = losses["pnl"].mean() if len(losses) else 0
    profit_factor = wins["pnl"].sum() / abs(losses["pnl"].sum()) if losses["pnl"].sum() != 0 else float("inf")
    total_pnl     = closed["pnl"].sum()
    total_return  = total_pnl / STARTING_CAPITAL * 100

    # Max drawdown from combined equity curve
    all_equity = []
    for r in results:
        all_equity.extend(r["equity_curve"])
    if all_equity:
        eq_series = pd.DataFrame(all_equity).groupby("date")["equity"].mean()
        roll_max  = eq_series.cummax()
        drawdown  = (eq_series - roll_max) / roll_max * 100
        max_dd    = drawdown.min()
    else:
        max_dd = 0.0

    # Buy-and-hold benchmark (average across symbols)
    years = (end - start).days / 365.25

    return {
        "period":         f"{start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}",
        "total_trades":   len(closed),
        "win_rate":       round(win_rate, 1),
        "avg_win":        round(avg_win, 2),
        "avg_loss":       round(avg_loss, 2),
        "profit_factor":  round(profit_factor, 2),
        "total_pnl":      round(total_pnl, 2),
        "total_return":   round(total_return, 2),
        "max_drawdown":   round(max_dd, 2),
        "years":          round(years, 1),
        "annualized_return": round(((1 + total_return / 100) ** (1 / years) - 1) * 100, 2) if years > 0 else 0,
        "by_symbol": {
            r["symbol"]: {
                "trades": len([t for t in r["trades"] if t["exit_reason"] != "end_of_data"]),
                "pnl":    round(sum(t["pnl"] for t in r["trades"] if t["exit_reason"] != "end_of_data"), 2),
            }
            for r in results
        },
    }


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_report(metrics: Dict, symbols: List[str]) -> None:
    sep = "─" * 60
    print(f"\n{'═' * 60}")
    print(f"  QuantShift Equity Bot Backtest Report")
    print(f"  Strategy: MA {SHORT_WINDOW}/{LONG_WINDOW} Crossover + RSI Filter + ATR SL/TP")
    print(f"  Symbols:  {', '.join(symbols)}")
    print(f"  Period:   {metrics['period']}  ({metrics['years']} years)")
    print(f"  Capital:  ${STARTING_CAPITAL:,.0f}")
    print(f"{'═' * 60}")

    if "error" in metrics:
        print(f"\n  ⚠  {metrics['error']}\n")
        return

    verdict = "✅ PASS" if metrics["win_rate"] >= 50 and metrics["profit_factor"] >= 1.2 and metrics["max_drawdown"] >= -25 else "⚠️  REVIEW"

    print(f"\n  {'OVERALL VERDICT':30} {verdict}")
    print(f"  {sep}")
    print(f"  {'Total Trades':30} {metrics['total_trades']}")
    print(f"  {'Win Rate':30} {metrics['win_rate']}%")
    print(f"  {'Avg Win':30} ${metrics['avg_win']:,.2f}")
    print(f"  {'Avg Loss':30} ${metrics['avg_loss']:,.2f}")
    print(f"  {'Profit Factor':30} {metrics['profit_factor']}x")
    print(f"  {sep}")
    print(f"  {'Total P&L':30} ${metrics['total_pnl']:,.2f}")
    print(f"  {'Total Return':30} {metrics['total_return']}%")
    print(f"  {'Annualized Return':30} {metrics['annualized_return']}%")
    print(f"  {'Max Drawdown':30} {metrics['max_drawdown']}%")
    print(f"  {sep}")
    print(f"\n  By Symbol:")
    for sym, data in metrics["by_symbol"].items():
        print(f"    {sym:8} {data['trades']:3} trades   P&L: ${data['pnl']:>10,.2f}")

    print(f"\n  Go/No-Go Criteria:")
    print(f"    Win Rate >= 50%:        {'✅' if metrics['win_rate'] >= 50 else '❌'}  ({metrics['win_rate']}%)")
    print(f"    Profit Factor >= 1.2x:  {'✅' if metrics['profit_factor'] >= 1.2 else '❌'}  ({metrics['profit_factor']}x)")
    print(f"    Max Drawdown >= -25%:   {'✅' if metrics['max_drawdown'] >= -25 else '❌'}  ({metrics['max_drawdown']}%)")
    print(f"    Annualized Return > 0%: {'✅' if metrics['annualized_return'] > 0 else '❌'}  ({metrics['annualized_return']}%)")
    print(f"\n{'═' * 60}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="QuantShift Equity Bot Backtest")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    parser.add_argument("--years",   type=int,   default=3)
    args = parser.parse_args()

    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=int(args.years * 365.25))

    print(f"\nFetching {args.years} years of daily bars for: {', '.join(args.symbols)} ...")

    results = []
    for symbol in args.symbols:
        print(f"  {symbol} ...", end=" ", flush=True)
        try:
            df = fetch_bars(symbol, start, end)
            if len(df) < LONG_WINDOW + 10:
                print(f"insufficient data ({len(df)} bars) — skipped")
                continue
            result = backtest_symbol(symbol, df)
            results.append(result)
            trades = len([t for t in result["trades"] if t["exit_reason"] != "end_of_data"])
            print(f"{len(df)} bars, {trades} trades")
        except Exception as e:
            print(f"ERROR: {e}")

    if not results:
        print("\nNo results — check API credentials or symbol names.")
        return

    metrics = calc_metrics(results, start, end)
    print_report(metrics, args.symbols)


if __name__ == "__main__":
    main()
