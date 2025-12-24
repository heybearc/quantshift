"""
Analytics utilities for the Alpaca Trading Bot.

This module provides functions for analyzing trading performance and generating reports.
"""
import os
import csv
import pandas as pd
from typing import Dict, Any, Optional, List

from alpaca_trading.utils.logging_config import setup_logger

# Set up logger
logger = setup_logger(__name__)

def summarize_performance(csv_path: str = "trade_history.csv") -> Dict[str, Any]:
    """
    Analyze trading performance from trade history CSV.
    
    Args:
        csv_path: Path to the CSV file containing trade history
        
    Returns:
        Dict containing performance metrics
    """
    if not os.path.exists(csv_path):
        logger.warning(f"No trade history file found at {csv_path}")
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate_percent": 0,
            "net_pnl": 0,
            "avg_pnl_per_trade": 0
        }

    df = pd.read_csv(csv_path)
    if df.empty:
        logger.warning("Trade history is empty")
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate_percent": 0,
            "net_pnl": 0,
            "avg_pnl_per_trade": 0
        }

    # Clean and prepare data
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['qty'] = pd.to_numeric(df['qty'], errors='coerce')
    df.dropna(subset=['price', 'qty'], inplace=True)

    # Sort by timestamp
    trades = df.sort_values(by='timestamp')
    trades['side_shift'] = trades['side'].shift(1)
    trades['symbol_shift'] = trades['symbol'].shift(1)

    # Calculate P&L for each trade
    pnl = []
    for i in range(1, len(trades)):
        if trades.iloc[i]['side'] == 'sell' and trades.iloc[i - 1]['side'] == 'buy' and trades.iloc[i]['symbol'] == trades.iloc[i - 1]['symbol']:
            profit = (trades.iloc[i]['price'] - trades.iloc[i - 1]['price']) * trades.iloc[i - 1]['qty']
            pnl.append(profit)

    # Calculate performance metrics
    total_trades = len(pnl)
    wins = sum(p > 0 for p in pnl)
    losses = sum(p < 0 for p in pnl)
    
    # Prepare results
    results = {
        "total_trades": total_trades,
        "winning_trades": wins,
        "losing_trades": losses,
        "win_rate_percent": round((wins / total_trades) * 100, 2) if total_trades > 0 else 0,
        "net_pnl": round(sum(pnl), 2),
        "avg_pnl_per_trade": round(sum(pnl) / total_trades, 2) if total_trades > 0 else 0
    }
    
    # Log results
    logger.info(f"Performance Summary:")
    logger.info(f"Total closed trades: {results['total_trades']}")
    logger.info(f"Winning trades: {results['winning_trades']} ({results['win_rate_percent']:.2f}%)")
    logger.info(f"Losing trades: {results['losing_trades']} ({100-results['win_rate_percent']:.2f}%)")
    logger.info(f"Net P&L: ${results['net_pnl']:.2f}")
    logger.info(f"Average P&L per trade: ${results['avg_pnl_per_trade']:.2f}")
    
    return results

def save_performance_summary(summary: Dict[str, Any], output_path: str = "performance_summary.csv") -> None:
    """
    Save performance summary to CSV file.
    
    Args:
        summary: Dictionary containing performance metrics
        output_path: Path to save the CSV file
    """
    with open(output_path, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=summary.keys())
        writer.writeheader()
        writer.writerow(summary)
    
    logger.info(f"Performance summary saved to {output_path}")

def generate_equity_curve(csv_path: str = "trade_history.csv", output_path: str = "equity_curve.csv") -> None:
    """
    Generate equity curve from trade history.
    
    Args:
        csv_path: Path to the CSV file containing trade history
        output_path: Path to save the equity curve CSV
    """
    if not os.path.exists(csv_path):
        logger.warning(f"No trade history file found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    if df.empty:
        logger.warning("Trade history is empty")
        return
    
    # Clean and prepare data
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['qty'] = pd.to_numeric(df['qty'], errors='coerce')
    df.dropna(subset=['price', 'qty'], inplace=True)
    
    # Sort by timestamp
    trades = df.sort_values(by='timestamp')
    
    # Calculate P&L for each trade
    pnl_data = []
    for i in range(1, len(trades)):
        if trades.iloc[i]['side'] == 'sell' and trades.iloc[i - 1]['side'] == 'buy' and trades.iloc[i]['symbol'] == trades.iloc[i - 1]['symbol']:
            profit = (trades.iloc[i]['price'] - trades.iloc[i - 1]['price']) * trades.iloc[i - 1]['qty']
            pnl_data.append({
                'timestamp': trades.iloc[i]['timestamp'],
                'symbol': trades.iloc[i]['symbol'],
                'pnl': profit
            })
    
    # Create equity curve DataFrame
    if pnl_data:
        equity_curve = pd.DataFrame(pnl_data)
        equity_curve['cumulative_pnl'] = equity_curve['pnl'].cumsum()
        equity_curve.to_csv(output_path, index=False)
        logger.info(f"Equity curve saved to {output_path}")
    else:
        logger.warning("No completed trades found to generate equity curve")

def analyze_performance(trade_history_path: str = "trade_history.csv") -> Dict[str, Any]:
    """
    Comprehensive performance analysis function.
    
    This function runs all performance analysis and generates all reports.
    
    Args:
        trade_history_path: Path to the CSV file containing trade history
        
    Returns:
        Dict containing performance metrics
    """
    # Generate performance summary
    summary = summarize_performance(trade_history_path)
    
    # Save performance summary to CSV
    save_performance_summary(summary)
    
    # Generate equity curve
    generate_equity_curve(trade_history_path)
    
    return summary
