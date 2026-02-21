#!/usr/bin/env python3
"""
Crypto Bot Backtest — MA 20/50 + RSI + MACD Strategy
Mirrors live crypto bot logic exactly, using daily data from Yahoo Finance.
"""

import sys
import argparse
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np


# Strategy parameters — match live bot exactly
MA_FAST = 20
MA_SLOW = 50
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_PERIOD = 14
ATR_SL_MULT = 2.0
ATR_TP_MULT = 4.0
RISK_PCT = 0.01
STARTING_CAPITAL = 100_000.0


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sma_fast"] = sma(df["close"], MA_FAST)
    df["sma_slow"] = sma(df["close"], MA_SLOW)
    df["rsi"] = rsi(df["close"], RSI_PERIOD)
    df["atr"] = atr(df["high"], df["low"], df["close"], ATR_PERIOD)
    macd_line, signal_line, histogram = macd(df["close"], MACD_FAST, MACD_SLOW, MACD_SIGNAL)
    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = histogram
    return df


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------

def fetch_bars(symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
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
# Signal generation — mirrors live crypto bot
# ---------------------------------------------------------------------------

def generate_signal(row: pd.Series, prev: pd.Series) -> Optional[str]:
    """BUY when MA fast crosses above slow AND RSI < 70 AND MACD > signal.
       SELL when MA fast crosses below slow AND RSI > 30."""
    
    if pd.isna(row["sma_fast"]) or pd.isna(row["sma_slow"]):
        return None
    if pd.isna(row["rsi"]) or pd.isna(row["macd"]) or pd.isna(row["macd_signal"]):
        return None
    
    # BUY: fast crosses above slow
    if row["sma_fast"] > row["sma_slow"] and prev["sma_fast"] <= prev["sma_slow"]:
        if row["rsi"] < RSI_OVERBOUGHT and row["macd"] > row["macd_signal"]:
            return "BUY"
    
    # SELL: fast crosses below slow
    elif row["sma_fast"] < row["sma_slow"] and prev["sma_fast"] >= prev["sma_slow"]:
        if row["rsi"] > RSI_OVERSOLD:
            return "SELL"
    
    return None


# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------

def backtest_symbol(symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
    df = add_indicators(df)
    
    cash = STARTING_CAPITAL
    position = None
    trades = []
    equity_curve = []
    
    for i in range(MA_SLOW + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        price = row["close"]
        date = df.index[i]
        
        signal = generate_signal(row, prev)
        
        # Entry
        if signal == "BUY" and position is None:
            atr_val = row["atr"] if not pd.isna(row["atr"]) else price * 0.02
            risk_dollars = cash * RISK_PCT
            qty = risk_dollars / (ATR_SL_MULT * atr_val)
            cost = qty * price
            
            if cost <= cash:
                position = {
                    "entry_price": price,
                    "qty": qty,
                    "stop_loss": price - (ATR_SL_MULT * atr_val),
                    "take_profit": price + (ATR_TP_MULT * atr_val),
                    "entry_date": date,
                }
                cash -= cost
        
        # Exit on signal
        elif signal == "SELL" and position is not None:
            pnl = (price - position["entry_price"]) * position["qty"]
            cash += (position["qty"] * price)
            trades.append({
                "entry_date": position["entry_date"],
                "exit_date": date,
                "entry_price": position["entry_price"],
                "exit_price": price,
                "qty": position["qty"],
                "pnl": pnl,
                "exit_reason": "sell_signal",
            })
            position = None
        
        # Check SL/TP
        elif position is not None:
            if price <= position["stop_loss"]:
                pnl = (position["stop_loss"] - position["entry_price"]) * position["qty"]
                cash += (position["qty"] * position["stop_loss"])
                trades.append({
                    "entry_date": position["entry_date"],
                    "exit_date": date,
                    "entry_price": position["entry_price"],
                    "exit_price": position["stop_loss"],
                    "qty": position["qty"],
                    "pnl": pnl,
                    "exit_reason": "stop_loss",
                })
                position = None
            elif price >= position["take_profit"]:
                pnl = (position["take_profit"] - position["entry_price"]) * position["qty"]
                cash += (position["qty"] * position["take_profit"])
                trades.append({
                    "entry_date": position["entry_date"],
                    "exit_date": date,
                    "entry_price": position["entry_price"],
                    "exit_price": position["take_profit"],
                    "qty": position["qty"],
                    "pnl": pnl,
                    "exit_reason": "take_profit",
                })
                position = None
        
        # Track equity
        equity = cash
        if position is not None:
            equity += position["qty"] * price
        equity_curve.append({"date": date, "equity": equity})
    
    # Close any open position at end
    if position is not None:
        final_price = df.iloc[-1]["close"]
        pnl = (final_price - position["entry_price"]) * position["qty"]
        cash += position["qty"] * final_price
        trades.append({
            "entry_date": position["entry_date"],
            "exit_date": df.index[-1],
            "entry_price": position["entry_price"],
            "exit_price": final_price,
            "qty": position["qty"],
            "pnl": pnl,
            "exit_reason": "end_of_data",
        })
    
    final_equity = cash
    total_pnl = final_equity - STARTING_CAPITAL
    total_return_pct = (total_pnl / STARTING_CAPITAL) * 100
    
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] < 0]
    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    
    avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["pnl"] for t in losses) / len(losses) if losses else 0
    
    total_wins = sum(t["pnl"] for t in wins)
    total_losses = abs(sum(t["pnl"] for t in losses))
    profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
    
    # Max drawdown
    peak = STARTING_CAPITAL
    max_dd = 0
    for point in equity_curve:
        if point["equity"] > peak:
            peak = point["equity"]
        dd = ((point["equity"] - peak) / peak) * 100
        if dd < max_dd:
            max_dd = dd
    
    return {
        "symbol": symbol,
        "trades": trades,
        "total_pnl": total_pnl,
        "total_return_pct": total_return_pct,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "final_equity": final_equity,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(results: List[Dict], years: float):
    total_trades = sum(len(r["trades"]) for r in results)
    total_pnl = sum(r["total_pnl"] for r in results)
    total_return = (total_pnl / STARTING_CAPITAL) * 100
    annualized_return = (((STARTING_CAPITAL + total_pnl) / STARTING_CAPITAL) ** (1 / years) - 1) * 100
    
    all_trades = [t for r in results for t in r["trades"]]
    wins = [t for t in all_trades if t["pnl"] > 0]
    losses = [t for t in all_trades if t["pnl"] < 0]
    overall_win_rate = (len(wins) / len(all_trades) * 100) if all_trades else 0
    
    avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["pnl"] for t in losses) / len(losses) if losses else 0
    
    total_wins = sum(t["pnl"] for t in wins)
    total_losses = abs(sum(t["pnl"] for t in losses))
    overall_pf = (total_wins / total_losses) if total_losses > 0 else 0
    
    max_dd = min(r["max_drawdown"] for r in results) if results else 0
    
    # Verdict
    verdict = "✅ GO" if (overall_win_rate >= 50 and overall_pf >= 1.2 and max_dd >= -25 and annualized_return > 0) else "⚠️  REVIEW"
    
    print("\n" + "=" * 60)
    print("  QuantShift Crypto Bot Backtest Report")
    print("  Strategy: MA 20/50 + RSI + MACD")
    print(f"  Symbols:  {', '.join(r['symbol'] for r in results)}")
    print(f"  Period:   {years:.1f} years (daily data)")
    print(f"  Capital:  ${STARTING_CAPITAL:,.0f}")
    print("=" * 60)
    print()
    print(f"  OVERALL VERDICT                {verdict}")
    print("  " + "-" * 58)
    print(f"  Total Trades                   {total_trades}")
    print(f"  Win Rate                       {overall_win_rate:.1f}%")
    print(f"  Avg Win                        ${avg_win:,.2f}")
    print(f"  Avg Loss                       ${avg_loss:,.2f}")
    print(f"  Profit Factor                  {overall_pf:.2f}x")
    print("  " + "-" * 58)
    print(f"  Total P&L                      ${total_pnl:,.2f}")
    print(f"  Total Return                   {total_return:.2f}%")
    print(f"  Annualized Return              {annualized_return:.2f}%")
    print(f"  Max Drawdown                   {max_dd:.2f}%")
    print("  " + "-" * 58)
    print()
    print("  By Symbol:")
    for r in results:
        closed_trades = [t for t in r["trades"] if t["exit_reason"] != "end_of_data"]
        print(f"    {r['symbol']:<10} {len(closed_trades):2} trades   P&L: ${r['total_pnl']:>10,.2f}")
    print()
    print("  Go/No-Go Criteria:")
    print(f"    Win Rate >= 50%:        {'✅' if overall_win_rate >= 50 else '❌'}  ({overall_win_rate:.1f}%)")
    print(f"    Profit Factor >= 1.2x:  {'✅' if overall_pf >= 1.2 else '❌'}  ({overall_pf:.2f}x)")
    print(f"    Max Drawdown >= -25%:   {'✅' if max_dd >= -25 else '❌'}  ({max_dd:.2f}%)")
    print(f"    Annualized Return > 0%: {'✅' if annualized_return > 0 else '❌'}  ({annualized_return:.2f}%)")
    print()
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Backtest crypto bot strategy")
    parser.add_argument("--symbols", nargs="+", default=["BTC-USD", "ETH-USD"], help="Crypto symbols")
    parser.add_argument("--years", type=float, default=2.0, help="Years of history")
    args = parser.parse_args()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=int(args.years * 365.25))

    print(f"\nFetching {args.years} years of daily bars for: {', '.join(args.symbols)} ...")

    results = []
    for symbol in args.symbols:
        print(f"  {symbol} ...", end=" ", flush=True)
        try:
            df = fetch_bars(symbol, start, end)
            if len(df) < MA_SLOW + 10:
                print(f"insufficient data ({len(df)} bars) — skipped")
                continue
            result = backtest_symbol(symbol, df)
            results.append(result)
            trades = len([t for t in result["trades"] if t["exit_reason"] != "end_of_data"])
            print(f"{len(df)} bars, {trades} trades")
        except Exception as e:
            print(f"ERROR: {e}")

    if not results:
        print("\nNo results — check API credentials or symbol names.\n")
        sys.exit(1)

    print_report(results, args.years)


if __name__ == "__main__":
    main()
