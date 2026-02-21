#!/usr/bin/env python3
"""
Breakout Momentum Strategy Backtest

Strategy Logic:
- Entry: Price breaks above 20-day high + volume > 1.5x average
- Exit: Trailing stop at 1.5×ATR OR price breaks below 10-day low
- Stop Loss: Entry - 2×ATR
- Take Profit: Entry + 4×ATR (2:1 reward/risk)

Target: >50% win rate, positive profit factor
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators for breakout strategy."""
    # 20-day high/low for breakout detection
    df['high_20'] = df['High'].rolling(window=20).max()
    df['low_10'] = df['Low'].rolling(window=10).min()
    
    # Volume moving average
    df['volume_ma'] = df['Volume'].rolling(window=20).mean()
    
    # Trend filter: 50-day SMA
    df['sma_50'] = df['Close'].rolling(window=50).mean()
    
    # ATR for position sizing and stops
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift(1))
    low_close = abs(df['Low'] - df['Close'].shift(1))
    df['tr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = df['tr'].rolling(window=14).mean()
    
    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate breakout signals.
    
    Entry: Price breaks above 20-day high + volume > 1.2x average + uptrend
    """
    df = df.copy()
    df['signal'] = 0
    
    # Vectorized signal generation
    # Price breaks above previous day's 20-day high
    price_breakout = df['Close'] > df['high_20'].shift(1)
    # Volume exceeds 1.2x the 20-day average (reduced from 1.5x)
    volume_surge = df['Volume'] > (df['volume_ma'] * 1.2)
    # Trend filter: price above 50-day SMA (only trade breakouts in uptrends)
    uptrend = df['Close'] > df['sma_50']
    
    # All conditions must be true
    df.loc[price_breakout & volume_surge & uptrend, 'signal'] = 1
    
    return df


def backtest_strategy(
    df: pd.DataFrame,
    initial_capital: float = 100000,
    risk_per_trade: float = 0.01
) -> Dict:
    """
    Backtest the breakout momentum strategy.
    
    Args:
        df: DataFrame with OHLCV data and indicators
        initial_capital: Starting capital
        risk_per_trade: Risk per trade as fraction of equity (0.01 = 1%)
    """
    capital = initial_capital
    position = None
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(len(df)):
        current_price = df['Close'].iloc[i]
        current_date = df.index[i]
        
        # Update equity curve
        if position:
            unrealized_pl = (current_price - position['entry_price']) * position['shares']
            current_equity = capital + unrealized_pl
        else:
            current_equity = capital
        equity_curve.append(current_equity)
        
        # Exit logic (check first)
        if position:
            # Exit conditions
            hit_stop = current_price <= position['stop_loss']
            hit_target = current_price >= position['take_profit']
            trailing_stop_hit = current_price <= position['trailing_stop']
            breakdown = df['Low'].iloc[i] < df['low_10'].iloc[i-1] if i > 0 else False
            
            if hit_stop or hit_target or trailing_stop_hit or breakdown:
                # Close position
                exit_price = current_price
                if hit_stop:
                    exit_price = position['stop_loss']
                    exit_reason = 'Stop Loss'
                elif hit_target:
                    exit_price = position['take_profit']
                    exit_reason = 'Take Profit'
                elif breakdown:
                    exit_reason = '10-day Low Break'
                else:
                    exit_reason = 'Trailing Stop'
                
                pl = (exit_price - position['entry_price']) * position['shares']
                capital += pl
                
                trades.append({
                    'entry_date': position['entry_date'],
                    'exit_date': current_date,
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'shares': position['shares'],
                    'pl': pl,
                    'pl_pct': (exit_price / position['entry_price'] - 1) * 100,
                    'exit_reason': exit_reason,
                    'days_held': (current_date - position['entry_date']).days
                })
                
                position = None
            else:
                # Update trailing stop (1.5×ATR below current price)
                atr = df['atr'].iloc[i]
                new_trailing_stop = current_price - (1.5 * atr)
                position['trailing_stop'] = max(position['trailing_stop'], new_trailing_stop)
        
        # Entry logic
        if position is None and df['signal'].iloc[i] == 1:
            atr = df['atr'].iloc[i]
            
            # Position sizing based on ATR risk
            risk_amount = capital * risk_per_trade
            risk_per_share = atr * 2.0  # 2×ATR stop
            shares = int(risk_amount / risk_per_share)
            
            if shares > 0:
                entry_price = current_price
                stop_loss = entry_price - (atr * 2.0)
                take_profit = entry_price + (atr * 4.0)  # 2:1 reward/risk
                trailing_stop = entry_price - (atr * 1.5)
                
                position = {
                    'entry_date': current_date,
                    'entry_price': entry_price,
                    'shares': shares,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'trailing_stop': trailing_stop,
                    'atr': atr
                }
    
    # Close any remaining position at end
    if position:
        exit_price = df['Close'].iloc[-1]
        pl = (exit_price - position['entry_price']) * position['shares']
        capital += pl
        
        trades.append({
            'entry_date': position['entry_date'],
            'exit_date': df.index[-1],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'shares': position['shares'],
            'pl': pl,
            'pl_pct': (exit_price / position['entry_price'] - 1) * 100,
            'exit_reason': 'End of Period',
            'days_held': (df.index[-1] - position['entry_date']).days
        })
    
    # Calculate metrics
    trades_df = pd.DataFrame(trades)
    
    if len(trades_df) == 0:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'total_return': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'trades': trades_df
        }
    
    winning_trades = trades_df[trades_df['pl'] > 0]
    losing_trades = trades_df[trades_df['pl'] <= 0]
    
    total_return = ((capital - initial_capital) / initial_capital) * 100
    win_rate = (len(winning_trades) / len(trades_df)) * 100
    
    total_wins = winning_trades['pl'].sum() if len(winning_trades) > 0 else 0
    total_losses = abs(losing_trades['pl'].sum()) if len(losing_trades) > 0 else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    # Calculate max drawdown
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    avg_win = winning_trades['pl'].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['pl'].mean() if len(losing_trades) > 0 else 0
    
    return {
        'total_trades': len(trades_df),
        'win_rate': win_rate,
        'total_return': total_return,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'final_capital': capital,
        'trades': trades_df,
        'equity_curve': equity_curve
    }


def run_backtest_for_symbol(symbol: str, years: int = 3) -> Dict:
    """Run backtest for a single symbol."""
    print(f"\n{'='*60}")
    print(f"Backtesting {symbol}")
    print(f"{'='*60}")
    
    # Fetch data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    print(f"Fetching data from {start_date.date()} to {end_date.date()}...")
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        print(f"No data available for {symbol}")
        return None
    
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    print(f"Data points: {len(df)}")
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Generate signals
    df = generate_signals(df)
    
    # Run backtest
    results = backtest_strategy(df)
    
    # Print results
    print(f"\n{symbol} Results:")
    print(f"  Total Trades: {results['total_trades']}")
    print(f"  Win Rate: {results['win_rate']:.2f}%")
    print(f"  Total Return: {results['total_return']:.2f}%")
    print(f"  Profit Factor: {results['profit_factor']:.2f}x")
    print(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"  Avg Win: ${results['avg_win']:.2f}")
    print(f"  Avg Loss: ${results['avg_loss']:.2f}")
    print(f"  Final Capital: ${results['final_capital']:.2f}")
    
    if results['total_trades'] > 0:
        print(f"\n  Exit Reasons:")
        exit_counts = results['trades']['exit_reason'].value_counts()
        for reason, count in exit_counts.items():
            print(f"    {reason}: {count} ({count/results['total_trades']*100:.1f}%)")
    
    return results


def main():
    """Run backtest on multiple symbols."""
    symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT']
    years = 3
    
    print("="*60)
    print("BREAKOUT MOMENTUM STRATEGY BACKTEST")
    print("="*60)
    print(f"\nStrategy Rules:")
    print(f"  Entry: Price breaks 20-day high + volume > 1.5x average")
    print(f"  Exit: Trailing stop (1.5×ATR) OR 10-day low break")
    print(f"  Stop Loss: Entry - 2×ATR")
    print(f"  Take Profit: Entry + 4×ATR (2:1 R/R)")
    print(f"  Position Size: 1% risk per trade")
    print(f"\nBacktest Period: {years} years")
    print(f"Symbols: {', '.join(symbols)}")
    
    all_results = {}
    
    for symbol in symbols:
        results = run_backtest_for_symbol(symbol, years)
        if results:
            all_results[symbol] = results
    
    # Aggregate results
    print(f"\n{'='*60}")
    print("AGGREGATE RESULTS")
    print(f"{'='*60}")
    
    total_trades = sum(r['total_trades'] for r in all_results.values())
    total_wins = sum(len(r['trades'][r['trades']['pl'] > 0]) for r in all_results.values())
    aggregate_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
    total_pl = sum(r['final_capital'] - 100000 for r in all_results.values())
    aggregate_return = (total_pl / (100000 * len(all_results))) * 100
    
    avg_profit_factor = np.mean([r['profit_factor'] for r in all_results.values() if r['profit_factor'] != float('inf')])
    avg_max_drawdown = np.mean([r['max_drawdown'] for r in all_results.values()])
    
    print(f"\nTotal Trades: {total_trades}")
    print(f"Aggregate Win Rate: {aggregate_win_rate:.2f}%")
    print(f"Aggregate Return: {aggregate_return:.2f}%")
    print(f"Avg Profit Factor: {avg_profit_factor:.2f}x")
    print(f"Avg Max Drawdown: {avg_max_drawdown:.2f}%")
    
    print(f"\n{'='*60}")
    print("STRATEGY EVALUATION")
    print(f"{'='*60}")
    
    if aggregate_win_rate >= 50 and aggregate_return > 0 and avg_profit_factor > 1.5:
        print("✅ PASS - Strategy meets criteria for implementation")
        print(f"   - Win rate {aggregate_win_rate:.1f}% >= 50%")
        print(f"   - Positive return: {aggregate_return:.2f}%")
        print(f"   - Profit factor {avg_profit_factor:.2f}x > 1.5")
    else:
        print("❌ FAIL - Strategy needs optimization")
        if aggregate_win_rate < 50:
            print(f"   - Win rate {aggregate_win_rate:.1f}% < 50%")
        if aggregate_return <= 0:
            print(f"   - Negative return: {aggregate_return:.2f}%")
        if avg_profit_factor <= 1.5:
            print(f"   - Profit factor {avg_profit_factor:.2f}x <= 1.5")


if __name__ == '__main__':
    main()
