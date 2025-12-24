"""
Notification module for the Alpaca Trading Bot.

This module handles all notification functionality including email alerts.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from alpaca_trading.core.config import config
from alpaca_trading.core.exceptions import TradingError, ConfigurationError

# Configure logger
logger = logging.getLogger(__name__)

class Notifier:
    """Handles all notification functionality for the trading bot."""
    
    def __init__(self):
        """Initialize the notifier with configuration."""
        self.enabled = all([
            config.email_host,
            config.email_port,
            config.email_user,
            config.email_pass,
            config.email_from,
            config.email_to
        ])
        if not self.enabled:
            logger.warning("Email notification is disabled due to incomplete configuration")
            logger.warning("Required email settings: EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, EMAIL_FROM, EMAIL_TO")
    
    def send_email(self, subject: str, body: str) -> bool:
        """
        Send an email alert.
        
        Args:
            subject: Email subject
            body: Email body content
            
        Returns:
            bool: True if email was sent successfully, False otherwise
            
        Raises:
            ConfigurationError: If email configuration is incomplete
            TradingError: If there's an error sending the email
        """
        if not self.enabled:
            logger.warning("Email notification is disabled, not sending: %s", subject)
            return False
            
        try:
            # Set up the email
            msg = MIMEMultipart()
            msg['From'] = config.email_from
            msg['To'] = config.email_to
            msg['Subject'] = f"[Trading Bot] {subject}"
            
            # Add body to email
            msg.attach(MIMEText(body, 'plain'))
            
            try:
                # Send the email using Brevo SMTP
                with smtplib.SMTP(config.email_host, config.email_port) as server:
                    server.starttls()
                    server.login(config.email_user, config.email_pass)
                    server.send_message(msg)
                
                logger.info("Email alert sent to %s: %s", config.email_to, subject)
                return True
                
            except Exception as e:
                logger.error("Failed to send email alert: %s", str(e))
                # Log the email that would have been sent
                logger.info("[Email would be sent] %s: %s", subject, body)
                return False
                
        except smtplib.SMTPException as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            raise TradingError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.exception(error_msg)
            raise TradingError(error_msg) from e

# Create a singleton instance of the notifier
notifier = Notifier()

# For backward compatibility
def send_email_alert(subject: str, body: str) -> bool:
    """
    Send an email alert (legacy function).
    
    This is kept for backward compatibility with existing code.
    """
    return notifier.send_email(subject, body)

# Additional alias for backward compatibility
def send_notification(subject: str, message: str) -> bool:
    """
    Send a notification (alias for send_email_alert).
    
    This is kept for backward compatibility with existing code.
    """
    return send_email_alert(subject, message)
