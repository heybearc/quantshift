#!/usr/bin/env python3
"""
RSI Mean Reversion Strategy Backtest
Entry: RSI < 30 (oversold) → BUY
Exit: RSI > 70 (overbought) OR price hits stop/target
Stop: 2× ATR below entry
Target: 3× ATR above entry (risk:reward = 1:1.5)
"""

import sys
import argparse
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
ATR_PERIOD = 14
ATR_SL_MULT = 2.0
ATR_TP_MULT = 3.0
RISK_PCT = 0.01
STARTING_CAPITAL = 100_000.0

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

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rsi"] = rsi(df["close"], RSI_PERIOD)
    df["atr"] = atr(df["high"], df["low"], df["close"], ATR_PERIOD)
    return df

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

def generate_signal(row: pd.Series, prev: pd.Series, has_position: bool) -> Optional[str]:
    """BUY when RSI crosses below 30, SELL when RSI crosses above 70."""
    if pd.isna(row["rsi"]) or pd.isna(prev["rsi"]):
        return None
    
    if not has_position and row["rsi"] < RSI_OVERSOLD and prev["rsi"] >= RSI_OVERSOLD:
        return "BUY"
    elif has_position and row["rsi"] > RSI_OVERBOUGHT and prev["rsi"] <= RSI_OVERBOUGHT:
        return "SELL"
    
    return None

def backtest_symbol(symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
    df = add_indicators(df)
    
    cash = STARTING_CAPITAL
    position = None
    trades = []
    equity_curve = []
    
    for i in range(RSI_PERIOD + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        price = row["close"]
        date = df.index[i]
        
        signal = generate_signal(row, prev, position is not None)
        
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
                "exit_reason": "rsi_overbought",
            })
            position = None
        
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
        
        equity = cash
        if position is not None:
            equity += position["qty"] * price
        equity_curve.append({"date": date, "equity": equity})
    
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
    
    verdict = "✅ GO" if (overall_win_rate >= 50 and overall_pf >= 1.2 and max_dd >= -25 and annualized_return > 0) else "⚠️  REVIEW"
    
    print("\n" + "=" * 60)
    print("  RSI Mean Reversion Strategy Backtest")
    print("  Entry: RSI < 30 (oversold)")
    print("  Exit: RSI > 70 (overbought) OR stop/target")
    print(f"  Symbols:  {', '.join(r['symbol'] for r in results)}")
    print(f"  Period:   {years:.1f} years")
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

def main():
    parser = argparse.ArgumentParser(description="Backtest RSI mean reversion strategy")
    parser.add_argument("--symbols", nargs="+", default=["SPY", "QQQ", "AAPL", "MSFT"], help="Symbols to test")
    parser.add_argument("--years", type=float, default=3.0, help="Years of history")
    args = parser.parse_args()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=int(args.years * 365.25))

    print(f"\nFetching {args.years} years of daily bars for: {', '.join(args.symbols)} ...")

    results = []
    for symbol in args.symbols:
        print(f"  {symbol} ...", end=" ", flush=True)
        try:
            df = fetch_bars(symbol, start, end)
            if len(df) < RSI_PERIOD + 10:
                print(f"insufficient data ({len(df)} bars) — skipped")
                continue
            result = backtest_symbol(symbol, df)
            results.append(result)
            trades = len([t for t in result["trades"] if t["exit_reason"] != "end_of_data"])
            print(f"{len(df)} bars, {trades} trades")
        except Exception as e:
            print(f"ERROR: {e}")

    if not results:
        print("\nNo results — check symbol names.\n")
        sys.exit(1)

    print_report(results, args.years)

if __name__ == "__main__":
    main()
