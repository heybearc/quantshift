"""
Email notification integration for equity trading bot.

Handles sending notifications for:
- Trade executions
- Daily summaries
- Error alerts
"""

import yaml
from datetime import datetime
from typing import Dict, Any, Optional
import structlog
from quantshift_core.notifications import EmailService

logger = structlog.get_logger()


class BotEmailNotifier:
    """
    Email notification manager for trading bot.
    
    Integrates with EmailService to send trade alerts, summaries, and error notifications.
    """
    
    def __init__(self, config_path: str = 'config/email_config.yaml'):
        """
        Initialize email notifier.
        
        Args:
            config_path: Path to email configuration file
        """
        # Load email configuration
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load email config: {e}")
            self.config = {'email': {'enabled': False}}
        
        # Initialize email service
        self.email_service = EmailService(self.config)
        self.enabled = self.email_service.enabled
        
        if self.enabled:
            logger.info("Email notifications enabled")
        else:
            logger.info("Email notifications disabled")
    
    def notify_trade_execution(
        self,
        signal: Dict[str, Any],
        order: Dict[str, Any],
        strategy_name: str
    ) -> bool:
        """
        Send trade execution notification.
        
        Args:
            signal: Trading signal that triggered the order
            order: Executed order details
            strategy_name: Name of the strategy
        
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            action = signal.get('action', 'UNKNOWN')
            symbol = signal.get('symbol', 'UNKNOWN')
            quantity = order.get('filled_qty', order.get('qty', 0))
            price = order.get('filled_avg_price', order.get('limit_price', 0))
            
            # Extract stop loss and take profit from signal
            stop_loss = signal.get('stop_loss')
            take_profit = signal.get('take_profit')
            risk_amount = signal.get('risk_amount')
            
            # Build signal details
            signal_details = {
                'Signal Type': signal.get('type', 'N/A'),
                'Confidence': signal.get('confidence', 'N/A'),
                'Entry Reason': signal.get('entry_reason', 'N/A'),
            }
            
            return self.email_service.send_trade_alert(
                action=action,
                symbol=symbol,
                quantity=quantity,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_amount=risk_amount,
                strategy=strategy_name,
                signal_details=signal_details
            )
            
        except Exception as e:
            logger.error(f"Failed to send trade notification: {e}", exc_info=True)
            return False
    
    def notify_daily_summary(
        self,
        account_data: Dict[str, Any],
        trades_today: int,
        pnl_today: float,
        open_positions: list,
        closed_trades: list,
        win_rate: Optional[float] = None
    ) -> bool:
        """
        Send daily performance summary.
        
        Args:
            account_data: Account information
            trades_today: Number of trades executed today
            pnl_today: Profit/loss for the day
            open_positions: List of open positions
            closed_trades: List of closed trades today
            win_rate: Win rate percentage
        
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            return self.email_service.send_daily_summary(
                date=datetime.utcnow(),
                trades_today=trades_today,
                pnl_today=pnl_today,
                open_positions=open_positions,
                closed_trades=closed_trades,
                account_balance=account_data.get('cash', 0),
                account_equity=account_data.get('equity', 0),
                win_rate=win_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}", exc_info=True)
            return False
    
    def notify_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send error notification.
        
        Args:
            error_type: Type of error
            error_message: Error message
            stack_trace: Full stack trace
            context: Additional context
        
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            return self.email_service.send_error_alert(
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                context=context
            )
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}", exc_info=True)
            return False
