"""
Notification system for QuantShift trading bot.

Supports email notifications for:
- Trade execution alerts
- Daily performance summaries
- Weekly reports
- Error notifications
"""

from .email_service import EmailService, EmailTemplate

__all__ = [
    'EmailService',
    'EmailTemplate',
]
