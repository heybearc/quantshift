"""Reporting utilities: persistent trade log and summary generation.

This is an extraction of *TradeLogger* from the original monolithic
`screener.py`.  No behaviour is changed, only the import path.
"""
from __future__ import annotations

import csv
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from .models import TradeRecord

logger = logging.getLogger(__name__)

__all__ = ["TradeLogger"]


class TradeLogger:  # noqa: D101
    def __init__(self, log_dir: str = "logs", log_file: str = "trade_log.csv") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.log_file = self.log_dir / log_file

        self.fieldnames: List[str] = TradeRecord.fieldnames()
        if not self.log_file.exists():
            with open(self.log_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    # ---------------------------------------------------------------------
    # Logging helpers
    # ---------------------------------------------------------------------
    def log_trade(self, trade_data: Dict[str, Any]) -> None:  # noqa: D401
        """Log a single trade (dict keys must match fieldnames)."""
        try:
            trade_data.setdefault("timestamp", datetime.utcnow().isoformat())
            trade_data.setdefault("date", datetime.utcnow().strftime("%Y-%m-%d"))
            if "amount" not in trade_data and {"qty", "price"}.issubset(trade_data):
                trade_data["amount"] = trade_data["qty"] * trade_data["price"]

            row = {field: trade_data.get(field, "") for field in self.fieldnames}
            with open(self.log_file, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writerow(row)
            logger.info(
                "Trade logged: %s %s %s @ $%.2f",
                trade_data.get("symbol"),
                trade_data.get("side").upper(),
                trade_data.get("qty"),
                trade_data.get("price"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error logging trade: %s", exc)

    # ------------------------------------------------------------------
    # Analytics helpers – history, summary, daily report
    # ------------------------------------------------------------------
    def _read_trades(self) -> List[TradeRecord]:
        if not self.log_file.exists():
            return []
        trades: List[TradeRecord] = []
        with open(self.log_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    trades.append(
                        TradeRecord(
                            timestamp=datetime.fromisoformat(row["timestamp"]),
                            date=row["date"],
                            symbol=row["symbol"],
                            side=row["side"],
                            qty=int(row["qty"] or 0),
                            price=float(row["price"] or 0),
                            amount=float(row["amount"] or 0),
                            order_id=row["order_id"],
                            status=row["status"],
                            reason=row.get("reason", ""),
                            atr=float(row.get("atr") or 0) if row.get("atr") else None,
                            atr_pct=float(row.get("atr_pct") or 0) if row.get("atr_pct") else None,
                            volume_ratio=float(row.get("volume_ratio") or 0)
                            if row.get("volume_ratio")
                            else None,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Skipping malformed row: %s", exc)
        return trades

    def get_trade_history(self, days: int = 30, symbol: str | None = None) -> List[TradeRecord]:
        cutoff = datetime.utcnow().date() - timedelta(days=days)
        return [
            t
            for t in self._read_trades()
            if (symbol is None or t.symbol == symbol) and datetime.fromisoformat(t.date).date() >= cutoff
        ]

    def get_trade_summary(self, days: int = 30) -> Dict[str, Any]:  # noqa: D401
        trades = self.get_trade_history(days=days)
        if not trades:
            return {}

        total_trades = len(trades)
        buy_trades = sum(1 for t in trades if t.side == "buy")
        sell_trades = total_trades - buy_trades
        volume = sum(t.qty for t in trades)
        amount = sum(t.amount for t in trades)
        avg_trade_size = amount / total_trades if total_trades else 0
        unique_symbols = len({t.symbol for t in trades})
        last_trade = max(trades, key=lambda t: t.timestamp).timestamp.isoformat()

        wins = sum(1 for t in trades if t.amount > 0)
        win_rate = wins / total_trades * 100 if total_trades else 0

        return {
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "unique_symbols": unique_symbols,
            "total_volume": volume,
            "total_amount": amount,
            "avg_trade_size": avg_trade_size,
            "win_rate": win_rate,
            "last_trade": last_trade,
        }

    def generate_daily_report(self) -> str:  # noqa: D401
        """Return plain-text summary for the last day – suitable for email."""
        summary = self.get_trade_summary(days=1)
        if not summary:
            return "No trades in the last day."

        return (
            "=== Daily Trading Report ===\n"
            f"Total Trades: {summary['total_trades']}\n"
            f"Buy Trades: {summary['buy_trades']}\n"
            f"Sell Trades: {summary['sell_trades']}\n"
            f"Unique Symbols: {summary['unique_symbols']}\n"
            f"Total Volume: {summary['total_volume']:,} shares\n"
            f"Total Amount: ${summary['total_amount']:.2f}\n"
            f"Average Trade Size: ${summary['avg_trade_size']:.2f}\n"
            f"Win Rate: {summary['win_rate']:.1f}%\n"
            f"Last Trade: {summary['last_trade']}\n"
            "============================="
        )
