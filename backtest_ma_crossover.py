#!/usr/bin/env python3
"""
Backtest MA Crossover Strategy - Phase 1 Validation

This script backtests the Moving Average Crossover strategy using:
- 2+ years of historical data (2022-2024)
- Broker-agnostic strategy framework
- Realistic costs (slippage, commissions)
- Comprehensive performance metrics

Success Criteria:
- Sharpe Ratio > 1.5
- Max Drawdown < 15%
- Win Rate > 50%
- Profit Factor > 1.5
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set up environment
os.environ['APCA_API_KEY_ID'] = 'PKUNCOV2CO3Y7XBI47CWOPCTBX'
os.environ['APCA_API_SECRET_KEY'] = '739TxLJoKbvSyV1yvioZxVkWZxdJSnXCPFPaN6ZdQjjL'

sys.path.insert(0, 'packages/core/src')

from quantshift_core.strategies import MACrossoverStrategy, Account, Position
from quantshift_core.backtesting import BacktestEngine

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

print("=" * 80)
print("MA Crossover Strategy Backtest - Phase 1 Validation")
print("=" * 80)

# Configuration
SYMBOL = 'SPY'
START_DATE = '2022-01-01'
END_DATE = '2024-12-31'
INITIAL_CAPITAL = 10000.0
COMMISSION = 0.0  # Alpaca zero commission
SLIPPAGE = 0.0005  # 5 basis points

# Strategy parameters
STRATEGY_CONFIG = {
    'short_window': 20,
    'long_window': 50,
    'atr_period': 14,
    'risk_per_trade': 0.02,
    'max_positions': 5,
    'volume_confirmation': True,
    'trend_confirmation': True,
    'support_resistance_filter': True
}

print(f"\nBacktest Configuration:")
print(f"  Symbol: {SYMBOL}")
print(f"  Period: {START_DATE} to {END_DATE}")
print(f"  Initial Capital: ${INITIAL_CAPITAL:,.2f}")
print(f"  Commission: ${COMMISSION:.4f} per trade")
print(f"  Slippage: {SLIPPAGE * 10000:.1f} bps")
print(f"\nStrategy Parameters:")
for key, value in STRATEGY_CONFIG.items():
    print(f"  {key}: {value}")

# Step 1: Fetch Historical Data
print(f"\n{'='*80}")
print("Step 1: Fetching Historical Data")
print("="*80)

try:
    data_client = StockHistoricalDataClient(
        api_key=os.getenv('APCA_API_KEY_ID'),
        secret_key=os.getenv('APCA_API_SECRET_KEY')
    )
    
    request = StockBarsRequest(
        symbol_or_symbols=SYMBOL,
        timeframe=TimeFrame.Day,
        start=datetime.strptime(START_DATE, '%Y-%m-%d'),
        end=datetime.strptime(END_DATE, '%Y-%m-%d'),
        feed=DataFeed.IEX
    )
    
    print(f"Fetching {SYMBOL} data from {START_DATE} to {END_DATE}...")
    bars = data_client.get_stock_bars(request)
    df = bars.df
    
    # Normalize DataFrame
    if hasattr(df.index, 'get_level_values'):
        if 'symbol' in df.index.names:
            df = df.xs(SYMBOL, level='symbol')
    
    df = df.sort_index()
    
    print(f"✓ Fetched {len(df)} bars")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"  Columns: {list(df.columns)}")
    
except Exception as e:
    print(f"✗ Error fetching data: {e}")
    sys.exit(1)

# Step 2: Initialize Strategy and Backtest Engine
print(f"\n{'='*80}")
print("Step 2: Initializing Strategy and Backtest Engine")
print("="*80)

strategy = MACrossoverStrategy(config=STRATEGY_CONFIG)
print(f"✓ Strategy initialized: {strategy.name}")

engine = BacktestEngine(
    initial_capital=INITIAL_CAPITAL,
    commission=COMMISSION,
    slippage=SLIPPAGE
)
print(f"✓ Backtest engine initialized")
print(f"  Initial capital: ${engine.initial_capital:,.2f}")
print(f"  Commission: ${engine.commission:.4f}")
print(f"  Slippage: {engine.slippage * 100:.3f}%")

# Step 3: Run Backtest
print(f"\n{'='*80}")
print("Step 3: Running Backtest")
print("="*80)

# Track progress
total_bars = len(df)
signals_generated = 0
trades_executed = 0

print(f"Processing {total_bars} bars...")

for i in range(STRATEGY_CONFIG['long_window'], len(df)):
    # Get market data up to current point
    current_date = df.index[i]
    market_data = df.iloc[:i+1].copy()
    
    # Add symbol attribute for strategy to access
    market_data.symbol = SYMBOL
    
    # Get current account state
    account = Account(
        equity=engine.capital + sum(p['market_value'] for p in engine.positions.values()),
        cash=engine.capital,
        buying_power=engine.capital,
        portfolio_value=engine.capital + sum(p['market_value'] for p in engine.positions.values()),
        positions_count=len(engine.positions)
    )
    
    # Convert engine positions to Position objects
    positions = []
    for symbol, pos_data in engine.positions.items():
        current_price = df.iloc[i]['close']
        positions.append(Position(
            symbol=symbol,
            quantity=pos_data['quantity'],
            entry_price=pos_data['entry_price'],
            current_price=current_price,
            market_value=current_price * pos_data['quantity'],
            unrealized_pl=(current_price - pos_data['entry_price']) * pos_data['quantity'],
            unrealized_plpc=((current_price - pos_data['entry_price']) / pos_data['entry_price']) * 100,
            side='long'
        ))
    
    # Generate signals
    signals = strategy.generate_signals(market_data, account, positions)
    
    if signals:
        signals_generated += len(signals)
        
        for signal in signals:
            # Execute signal in backtest
            if signal.signal_type.value == 'buy':
                success = engine.execute_trade(
                    symbol=signal.symbol,
                    action='BUY',
                    price=df.iloc[i]['close'],
                    quantity=signal.position_size,
                    timestamp=current_date,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit
                )
                if success:
                    trades_executed += 1
                    
            elif signal.signal_type.value == 'sell':
                success = engine.execute_trade(
                    symbol=signal.symbol,
                    action='SELL',
                    price=df.iloc[i]['close'],
                    quantity=signal.position_size,
                    timestamp=current_date
                )
                if success:
                    trades_executed += 1
    
    # Check stops
    current_prices = {SYMBOL: df.iloc[i]['close']}
    for symbol, pos in list(engine.positions.items()):
        if engine.check_stops(symbol, current_prices[symbol], current_date):
            trades_executed += 1
    
    # Update equity curve
    engine.update_equity(current_date, current_prices)
    
    # Progress indicator
    if (i - STRATEGY_CONFIG['long_window']) % 50 == 0:
        progress = ((i - STRATEGY_CONFIG['long_window']) / (total_bars - STRATEGY_CONFIG['long_window'])) * 100
        print(f"  Progress: {progress:.1f}% - Signals: {signals_generated}, Trades: {trades_executed}")

print(f"\n✓ Backtest complete")
print(f"  Total signals generated: {signals_generated}")
print(f"  Total trades executed: {trades_executed}")

# Step 4: Calculate Performance Metrics
print(f"\n{'='*80}")
print("Step 4: Performance Metrics")
print("="*80)

metrics = engine.get_metrics()

if 'error' in metrics:
    print(f"✗ Error calculating metrics: {metrics['error']}")
    sys.exit(1)

print(f"\n📊 Trading Statistics:")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Winning Trades: {metrics['winning_trades']}")
print(f"  Losing Trades: {metrics['losing_trades']}")
print(f"  Win Rate: {metrics['win_rate']:.2f}%")
print(f"  Average Win: ${metrics['avg_win']:.2f}")
print(f"  Average Loss: ${metrics['avg_loss']:.2f}")
print(f"  Profit Factor: {metrics['profit_factor']:.2f}")

print(f"\n💰 Returns:")
print(f"  Total Return: {metrics['total_return']:.2f}%")
print(f"  Final Equity: ${metrics['final_equity']:,.2f}")
print(f"  Initial Capital: ${INITIAL_CAPITAL:,.2f}")
print(f"  Profit/Loss: ${metrics['final_equity'] - INITIAL_CAPITAL:,.2f}")

print(f"\n📉 Risk Metrics:")
print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"  Avg Hold Time: {metrics['avg_hold_time_hours']:.1f} hours")

# Step 5: Validation Against Targets
print(f"\n{'='*80}")
print("Step 5: Validation Against Targets")
print("="*80)

targets = {
    'Sharpe Ratio': {'actual': metrics['sharpe_ratio'], 'target': 1.5, 'higher_better': True},
    'Max Drawdown': {'actual': abs(metrics['max_drawdown']), 'target': 15.0, 'higher_better': False},
    'Win Rate': {'actual': metrics['win_rate'], 'target': 50.0, 'higher_better': True},
    'Profit Factor': {'actual': metrics['profit_factor'], 'target': 1.5, 'higher_better': True}
}

all_passed = True
for metric_name, data in targets.items():
    if data['higher_better']:
        passed = data['actual'] >= data['target']
        symbol = '✓' if passed else '✗'
        comparison = '>=' 
    else:
        passed = data['actual'] <= data['target']
        symbol = '✓' if passed else '✗'
        comparison = '<='
    
    all_passed = all_passed and passed
    print(f"  {symbol} {metric_name}: {data['actual']:.2f} {comparison} {data['target']:.2f}")

# Step 6: Generate Report
print(f"\n{'='*80}")
print("Step 6: Generating Report")
print("="*80)

# Create reports directory
reports_dir = Path('reports')
reports_dir.mkdir(exist_ok=True)

# Save equity curve
equity_df = engine.get_equity_curve_df()
equity_df.to_csv(reports_dir / 'equity_curve.csv')
print(f"✓ Saved equity curve to reports/equity_curve.csv")

# Save trades
trades_df = engine.get_trades_df()
if not trades_df.empty:
    trades_df.to_csv(reports_dir / 'trades.csv')
    print(f"✓ Saved {len(trades_df)} trades to reports/trades.csv")

# Create visualization
try:
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Equity Curve
    axes[0].plot(equity_df['timestamp'], equity_df['equity'], label='Portfolio Value', linewidth=2)
    axes[0].axhline(y=INITIAL_CAPITAL, color='gray', linestyle='--', label='Initial Capital')
    axes[0].set_title(f'{SYMBOL} MA Crossover Strategy - Equity Curve', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Date')
    axes[0].set_ylabel('Portfolio Value ($)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Drawdown
    equity_series = pd.Series(equity_df['equity'].values, index=equity_df['timestamp'])
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series - rolling_max) / rolling_max * 100
    
    axes[1].fill_between(drawdown.index, drawdown, 0, alpha=0.3, color='red')
    axes[1].plot(drawdown.index, drawdown, color='red', linewidth=1)
    axes[1].set_title('Drawdown (%)', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Date')
    axes[1].set_ylabel('Drawdown (%)')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(reports_dir / 'backtest_results.png', dpi=150, bbox_inches='tight')
    print(f"✓ Saved visualization to reports/backtest_results.png")
    
except Exception as e:
    print(f"⚠ Could not create visualization: {e}")

# Save summary report
report_path = reports_dir / 'backtest_summary.txt'
with open(report_path, 'w') as f:
    f.write("="*80 + "\n")
    f.write("MA Crossover Strategy Backtest - Summary Report\n")
    f.write("="*80 + "\n\n")
    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    f.write("Configuration:\n")
    f.write(f"  Symbol: {SYMBOL}\n")
    f.write(f"  Period: {START_DATE} to {END_DATE}\n")
    f.write(f"  Initial Capital: ${INITIAL_CAPITAL:,.2f}\n")
    f.write(f"  Strategy: MA({STRATEGY_CONFIG['short_window']}/{STRATEGY_CONFIG['long_window']})\n\n")
    
    f.write("Performance Metrics:\n")
    for key, value in metrics.items():
        if isinstance(value, float):
            f.write(f"  {key}: {value:.2f}\n")
        else:
            f.write(f"  {key}: {value}\n")
    
    f.write("\nValidation Results:\n")
    for metric_name, data in targets.items():
        passed = '✓ PASS' if (data['higher_better'] and data['actual'] >= data['target']) or \
                            (not data['higher_better'] and data['actual'] <= data['target']) else '✗ FAIL'
        f.write(f"  {metric_name}: {passed}\n")
    
    f.write(f"\nOverall Result: {'✓ STRATEGY VALIDATED' if all_passed else '✗ STRATEGY FAILED VALIDATION'}\n")

print(f"✓ Saved summary report to reports/backtest_summary.txt")

# Final Decision
print(f"\n{'='*80}")
print("BACKTEST RESULTS")
print("="*80)

if all_passed:
    print("\n✓ ✓ ✓ STRATEGY VALIDATED ✓ ✓ ✓")
    print("\nThe MA Crossover strategy meets all performance targets.")
    print("Recommendation: PROCEED to Phase 2 (Bot Integration)")
else:
    print("\n✗ ✗ ✗ STRATEGY FAILED VALIDATION ✗ ✗ ✗")
    print("\nThe strategy did not meet all performance targets.")
    print("Recommendation: REFINE strategy parameters or try different strategy")

print(f"\n{'='*80}\n")
