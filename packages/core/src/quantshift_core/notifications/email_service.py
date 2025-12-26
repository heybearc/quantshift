"""
Email notification service for QuantShift trading bot.

Handles sending trade alerts, daily summaries, weekly reports, and error notifications.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class EmailTemplate:
    """Email template configuration."""
    subject: str
    from_name: str
    html_template: str
    text_template: Optional[str] = None


class EmailService:
    """
    Email notification service using Gmail SMTP.
    
    Supports:
    - Trade execution alerts
    - Daily performance summaries
    - Weekly reports
    - Error notifications
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize email service.
        
        Args:
            config: Email configuration dictionary
        """
        self.config = config
        self.enabled = config.get('email', {}).get('enabled', False)
        
        if not self.enabled:
            logger.info("Email notifications disabled")
            return
        
        # SMTP configuration
        smtp_config = config.get('email', {}).get('smtp', {})
        self.smtp_host = smtp_config.get('host', 'smtp.gmail.com')
        self.smtp_port = smtp_config.get('port', 587)
        self.use_tls = smtp_config.get('use_tls', True)
        
        # Get credentials from environment variables
        self.username = os.getenv('EMAIL_USERNAME')
        self.password = os.getenv('EMAIL_PASSWORD')
        
        if not self.username or not self.password:
            logger.warning(
                "Email credentials not found in environment variables. "
                "Set EMAIL_USERNAME and EMAIL_PASSWORD to enable email notifications."
            )
            self.enabled = False
            return
        
        # Recipients
        recipients = config.get('email', {}).get('recipients', {})
        self.alert_recipients = recipients.get('alerts', [])
        self.daily_recipients = recipients.get('daily_summary', [])
        self.weekly_recipients = recipients.get('weekly_report', [])
        self.error_recipients = recipients.get('errors', [])
        
        # Notification settings
        self.notifications = config.get('email', {}).get('notifications', {})
        
        # Rate limiting
        rate_limits = config.get('email', {}).get('rate_limits', {})
        self.max_emails_per_hour = rate_limits.get('max_emails_per_hour', 50)
        self.max_emails_per_day = rate_limits.get('max_emails_per_day', 200)
        
        # Track sent emails for rate limiting
        self.emails_sent_hour = []
        self.emails_sent_day = []
        
        logger.info(
            "Email service initialized",
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
            username=self.username
        )
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.utcnow()
        
        # Clean up old timestamps
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        self.emails_sent_hour = [ts for ts in self.emails_sent_hour if ts > hour_ago]
        self.emails_sent_day = [ts for ts in self.emails_sent_day if ts > day_ago]
        
        # Check limits
        if len(self.emails_sent_hour) >= self.max_emails_per_hour:
            logger.warning("Email rate limit reached (hourly)")
            return False
        
        if len(self.emails_sent_day) >= self.max_emails_per_day:
            logger.warning("Email rate limit reached (daily)")
            return False
        
        return True
    
    def _send_email(
        self,
        to_addresses: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
            attachments: List of attachments (optional)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Email service disabled, skipping send")
            return False
        
        if not to_addresses:
            logger.debug("No recipients specified, skipping send")
            return False
        
        if not self._check_rate_limit():
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"QuantShift Trading Bot <{self.username}>"
            msg['To'] = ', '.join(to_addresses)
            
            # Add text body
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Add HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    # Handle image attachments
                    if attachment.get('type') == 'image':
                        img = MIMEImage(attachment['data'])
                        img.add_header('Content-ID', f"<{attachment['cid']}>")
                        msg.attach(img)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            # Track for rate limiting
            now = datetime.utcnow()
            self.emails_sent_hour.append(now)
            self.emails_sent_day.append(now)
            
            logger.info(
                "Email sent successfully",
                subject=subject,
                recipients=len(to_addresses)
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False
    
    def send_trade_alert(
        self,
        action: str,
        symbol: str,
        quantity: int,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        risk_amount: Optional[float] = None,
        strategy: Optional[str] = None,
        signal_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send trade execution alert.
        
        Args:
            action: 'BUY' or 'SELL'
            symbol: Stock symbol
            quantity: Number of shares
            price: Execution price
            stop_loss: Stop loss price
            take_profit: Take profit price
            risk_amount: Dollar amount at risk
            strategy: Strategy name
            signal_details: Additional signal information
        
        Returns:
            True if email sent successfully
        """
        if not self.notifications.get('trade_alerts', {}).get('enabled', True):
            return False
        
        # Determine if we should send based on action
        if action.upper() == 'BUY' and not self.notifications.get('trade_alerts', {}).get('send_on_entry', True):
            return False
        if action.upper() == 'SELL' and not self.notifications.get('trade_alerts', {}).get('send_on_exit', True):
            return False
        
        # Build email
        subject = f"🔔 Trade Alert: {action} {symbol}"
        
        # Calculate potential profit
        potential_profit = None
        risk_reward = None
        if action.upper() == 'BUY' and take_profit and stop_loss:
            potential_profit = (take_profit - price) * quantity
            risk = (price - stop_loss) * quantity
            if risk > 0:
                risk_reward = potential_profit / risk
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .trade-details {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #2c3e50; }}
                .action-buy {{ color: #27ae60; font-weight: bold; font-size: 24px; }}
                .action-sell {{ color: #e74c3c; font-weight: bold; font-size: 24px; }}
                .footer {{ text-align: center; padding: 15px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Trade Execution Alert</h1>
                </div>
                <div class="content">
                    <div class="trade-details">
                        <div style="text-align: center; margin-bottom: 20px;">
                            <span class="action-{action.lower()}">{action.upper()}</span>
                            <h2 style="margin: 10px 0;">{symbol}</h2>
                        </div>
                        
                        <div class="detail-row">
                            <span class="label">Quantity:</span>
                            <span class="value">{quantity} shares</span>
                        </div>
                        
                        <div class="detail-row">
                            <span class="label">Price:</span>
                            <span class="value">${price:.2f}</span>
                        </div>
                        
                        <div class="detail-row">
                            <span class="label">Total Value:</span>
                            <span class="value">${price * quantity:.2f}</span>
                        </div>
                        
                        {f'''
                        <div class="detail-row">
                            <span class="label">Stop Loss:</span>
                            <span class="value">${stop_loss:.2f}</span>
                        </div>
                        ''' if stop_loss else ''}
                        
                        {f'''
                        <div class="detail-row">
                            <span class="label">Take Profit:</span>
                            <span class="value">${take_profit:.2f}</span>
                        </div>
                        ''' if take_profit else ''}
                        
                        {f'''
                        <div class="detail-row">
                            <span class="label">Risk Amount:</span>
                            <span class="value">${risk_amount:.2f}</span>
                        </div>
                        ''' if risk_amount else ''}
                        
                        {f'''
                        <div class="detail-row">
                            <span class="label">Potential Profit:</span>
                            <span class="value">${potential_profit:.2f}</span>
                        </div>
                        ''' if potential_profit else ''}
                        
                        {f'''
                        <div class="detail-row">
                            <span class="label">Risk/Reward:</span>
                            <span class="value">{risk_reward:.2f}:1</span>
                        </div>
                        ''' if risk_reward else ''}
                        
                        {f'''
                        <div class="detail-row">
                            <span class="label">Strategy:</span>
                            <span class="value">{strategy}</span>
                        </div>
                        ''' if strategy else ''}
                        
                        <div class="detail-row">
                            <span class="label">Time:</span>
                            <span class="value">{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</span>
                        </div>
                    </div>
                    
                    {f'''
                    <div style="margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 5px;">
                        <h3 style="margin-top: 0;">Signal Details</h3>
                        <pre style="font-size: 12px; overflow-x: auto;">{signal_details}</pre>
                    </div>
                    ''' if signal_details else ''}
                </div>
                <div class="footer">
                    <p>QuantShift Trading Bot - Automated Trade Notification</p>
                    <p>This is an automated message. Do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_addresses=self.alert_recipients,
            subject=subject,
            html_body=html_body
        )
    
    def send_daily_summary(
        self,
        date: datetime,
        trades_today: int,
        pnl_today: float,
        open_positions: List[Dict[str, Any]],
        closed_trades: List[Dict[str, Any]],
        account_balance: float,
        account_equity: float,
        win_rate: Optional[float] = None
    ) -> bool:
        """
        Send daily performance summary.
        
        Args:
            date: Date for the summary
            trades_today: Number of trades executed
            pnl_today: Profit/loss for the day
            open_positions: List of open positions
            closed_trades: List of closed trades
            account_balance: Cash balance
            account_equity: Total equity
            win_rate: Win rate percentage
        
        Returns:
            True if email sent successfully
        """
        if not self.notifications.get('daily_summary', {}).get('enabled', True):
            return False
        
        subject = f"📊 Daily Summary: {date.strftime('%Y-%m-%d')}"
        
        # Build open positions HTML
        positions_html = ""
        if open_positions:
            positions_html = "<h3>Open Positions</h3><table style='width: 100%; border-collapse: collapse;'>"
            positions_html += "<tr style='background: #f0f0f0;'><th>Symbol</th><th>Qty</th><th>Entry</th><th>Current</th><th>P&L</th></tr>"
            for pos in open_positions:
                pnl_color = '#27ae60' if pos.get('unrealized_pl', 0) >= 0 else '#e74c3c'
                positions_html += f"""
                <tr style='border-bottom: 1px solid #ddd;'>
                    <td style='padding: 8px;'>{pos['symbol']}</td>
                    <td style='padding: 8px;'>{pos['quantity']}</td>
                    <td style='padding: 8px;'>${pos['entry_price']:.2f}</td>
                    <td style='padding: 8px;'>${pos['current_price']:.2f}</td>
                    <td style='padding: 8px; color: {pnl_color};'>${pos.get('unrealized_pl', 0):.2f}</td>
                </tr>
                """
            positions_html += "</table>"
        else:
            positions_html = "<p>No open positions</p>"
        
        # Build closed trades HTML
        trades_html = ""
        if closed_trades:
            trades_html = "<h3>Closed Trades Today</h3><table style='width: 100%; border-collapse: collapse;'>"
            trades_html += "<tr style='background: #f0f0f0;'><th>Symbol</th><th>Action</th><th>Qty</th><th>Price</th><th>P&L</th></tr>"
            for trade in closed_trades:
                pnl_color = '#27ae60' if trade.get('pnl', 0) >= 0 else '#e74c3c'
                trades_html += f"""
                <tr style='border-bottom: 1px solid #ddd;'>
                    <td style='padding: 8px;'>{trade['symbol']}</td>
                    <td style='padding: 8px;'>{trade['action']}</td>
                    <td style='padding: 8px;'>{trade['quantity']}</td>
                    <td style='padding: 8px;'>${trade['price']:.2f}</td>
                    <td style='padding: 8px; color: {pnl_color};'>${trade.get('pnl', 0):.2f}</td>
                </tr>
                """
            trades_html += "</table>"
        else:
            trades_html = "<p>No trades closed today</p>"
        
        pnl_color = '#27ae60' if pnl_today >= 0 else '#e74c3c'
        pnl_symbol = '+' if pnl_today >= 0 else ''
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #34495e; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .summary-box {{ background: white; padding: 20px; margin: 15px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric {{ display: inline-block; width: 48%; padding: 15px; margin: 1%; background: #ecf0f1; border-radius: 5px; text-align: center; }}
                .metric-label {{ font-size: 14px; color: #7f8c8d; }}
                .metric-value {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
                table {{ margin: 15px 0; }}
                th {{ padding: 10px; text-align: left; }}
                .footer {{ text-align: center; padding: 15px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Daily Performance Summary</h1>
                    <p>{date.strftime('%A, %B %d, %Y')}</p>
                </div>
                <div class="content">
                    <div class="summary-box">
                        <h2 style="margin-top: 0;">Today's Performance</h2>
                        <div>
                            <div class="metric">
                                <div class="metric-label">Trades Today</div>
                                <div class="metric-value">{trades_today}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">P&L Today</div>
                                <div class="metric-value" style="color: {pnl_color};">{pnl_symbol}${abs(pnl_today):.2f}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Account Balance</div>
                                <div class="metric-value">${account_balance:.2f}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Total Equity</div>
                                <div class="metric-value">${account_equity:.2f}</div>
                            </div>
                            {f'''
                            <div class="metric">
                                <div class="metric-label">Win Rate</div>
                                <div class="metric-value">{win_rate:.1f}%</div>
                            </div>
                            ''' if win_rate is not None else ''}
                        </div>
                    </div>
                    
                    <div class="summary-box">
                        {positions_html}
                    </div>
                    
                    <div class="summary-box">
                        {trades_html}
                    </div>
                </div>
                <div class="footer">
                    <p>QuantShift Trading Bot - Daily Summary</p>
                    <p>This is an automated message. Do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_addresses=self.daily_recipients,
            subject=subject,
            html_body=html_body
        )
    
    def send_error_alert(
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
            context: Additional context information
        
        Returns:
            True if email sent successfully
        """
        if not self.notifications.get('error_alerts', {}).get('enabled', True):
            return False
        
        subject = f"⚠️ Bot Error: {error_type}"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #e74c3c; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .error-box {{ background: #fff5f5; padding: 15px; margin: 15px 0; border-left: 4px solid #e74c3c; border-radius: 5px; }}
                pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
                .footer {{ text-align: center; padding: 15px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Bot Error Alert</h1>
                </div>
                <div class="content">
                    <div class="error-box">
                        <h3 style="margin-top: 0; color: #e74c3c;">Error Type: {error_type}</h3>
                        <p><strong>Message:</strong> {error_message}</p>
                        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                    </div>
                    
                    {f'''
                    <div style="margin-top: 20px;">
                        <h3>Stack Trace:</h3>
                        <pre>{stack_trace}</pre>
                    </div>
                    ''' if stack_trace and self.notifications.get('error_alerts', {}).get('include_stack_trace', True) else ''}
                    
                    {f'''
                    <div style="margin-top: 20px;">
                        <h3>Context:</h3>
                        <pre>{context}</pre>
                    </div>
                    ''' if context else ''}
                    
                    <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 5px;">
                        <p><strong>Action Required:</strong> Please check the bot logs and resolve the issue.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>QuantShift Trading Bot - Error Alert</p>
                    <p>This is an automated message. Do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to_addresses=self.error_recipients,
            subject=subject,
            html_body=html_body
        )
