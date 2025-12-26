#!/usr/bin/env python3
"""
Test script for email notification system.

Tests:
1. Email service initialization
2. Trade alert sending
3. Daily summary sending
4. Error alert sending
"""

import os
import sys
from datetime import datetime

# Add packages to path
sys.path.insert(0, 'packages/core/src')

from quantshift_core.notifications import EmailService
from apps.bots.equity.email_integration import BotEmailNotifier


def test_email_service():
    """Test email service initialization and basic functionality."""
    print("=" * 60)
    print("Testing Email Notification System")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("[1] Checking environment variables...")
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    
    if not email_username or not email_password:
        print("❌ EMAIL_USERNAME or EMAIL_PASSWORD not set")
        print()
        print("To enable email notifications:")
        print("1. Generate Gmail App Password:")
        print("   - Go to https://myaccount.google.com/apppasswords")
        print("   - Create new app password for 'Mail'")
        print("2. Set environment variables:")
        print("   export EMAIL_USERNAME='your-email@gmail.com'")
        print("   export EMAIL_PASSWORD='your-app-password'")
        print()
        return False
    
    print(f"✓ EMAIL_USERNAME: {email_username}")
    print(f"✓ EMAIL_PASSWORD: {'*' * len(email_password)}")
    print()
    
    # Initialize email notifier
    print("[2] Initializing email notifier...")
    try:
        notifier = BotEmailNotifier(config_path='config/email_config.yaml')
        if notifier.enabled:
            print("✓ Email notifier initialized successfully")
        else:
            print("⚠️  Email notifier initialized but disabled")
            return False
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    print()
    
    # Test trade alert
    print("[3] Testing trade alert...")
    try:
        signal = {
            'action': 'BUY',
            'symbol': 'SPY',
            'type': 'MA_CROSSOVER',
            'confidence': 0.85,
            'entry_reason': 'MA 5 crossed above MA 20',
            'stop_loss': 590.00,
            'take_profit': 610.00,
            'risk_amount': 10.00
        }
        
        order = {
            'filled_qty': 2,
            'filled_avg_price': 595.00,
            'status': 'filled'
        }
        
        result = notifier.notify_trade_execution(
            signal=signal,
            order=order,
            strategy_name='MA Crossover (5/20)'
        )
        
        if result:
            print("✓ Trade alert sent successfully")
        else:
            print("⚠️  Trade alert not sent (check recipients in config)")
    except Exception as e:
        print(f"❌ Failed to send trade alert: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Test daily summary
    print("[4] Testing daily summary...")
    try:
        account_data = {
            'cash': 980.00,
            'equity': 1010.00
        }
        
        open_positions = [
            {
                'symbol': 'SPY',
                'quantity': 2,
                'entry_price': 595.00,
                'current_price': 600.00,
                'unrealized_pl': 10.00
            }
        ]
        
        closed_trades = [
            {
                'symbol': 'QQQ',
                'action': 'SELL',
                'quantity': 1,
                'price': 450.00,
                'pnl': 15.00
            }
        ]
        
        result = notifier.notify_daily_summary(
            account_data=account_data,
            trades_today=2,
            pnl_today=15.00,
            open_positions=open_positions,
            closed_trades=closed_trades,
            win_rate=66.7
        )
        
        if result:
            print("✓ Daily summary sent successfully")
        else:
            print("⚠️  Daily summary not sent (check recipients in config)")
    except Exception as e:
        print(f"❌ Failed to send daily summary: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Test error alert
    print("[5] Testing error alert...")
    try:
        result = notifier.notify_error(
            error_type='TestError',
            error_message='This is a test error notification',
            stack_trace='Traceback (most recent call last):\n  File "test.py", line 1, in <module>\n    raise Exception("Test")',
            context={'bot': 'equity-bot', 'test': True}
        )
        
        if result:
            print("✓ Error alert sent successfully")
        else:
            print("⚠️  Error alert not sent (check recipients in config)")
    except Exception as e:
        print(f"❌ Failed to send error alert: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    print("=" * 60)
    print("Email Notification Test Complete")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Check your email inbox for test messages")
    print("2. Update config/email_config.yaml with your email addresses")
    print("3. Integrate with run_bot_v2.py for live notifications")
    print()
    
    return True


if __name__ == '__main__':
    test_email_service()
