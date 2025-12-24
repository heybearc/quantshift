"""
Market Calendar Utility
Handles market hours and trading day calculations
"""

import pandas as pd
from datetime import datetime, time, timedelta
import pytz
from typing import Optional
import logging

from alpaca_trading.utils.logging_config import setup_logger

logger = setup_logger(__name__)

class MarketCalendar:
    """Utility class for market calendar operations"""
    
    def __init__(self):
        self.eastern_tz = pytz.timezone('US/Eastern')
        
        # Market hours (Eastern Time)
        self.market_open_time = time(9, 30)  # 9:30 AM ET
        self.market_close_time = time(16, 0)  # 4:00 PM ET
        
        # Pre-market and after-hours
        self.pre_market_start = time(4, 0)   # 4:00 AM ET
        self.after_hours_end = time(20, 0)   # 8:00 PM ET
        
        # Market holidays (simplified list - you may want to use a more comprehensive source)
        self.market_holidays_2024 = [
            datetime(2024, 1, 1),   # New Year's Day
            datetime(2024, 1, 15),  # Martin Luther King Jr. Day
            datetime(2024, 2, 19),  # Presidents' Day
            datetime(2024, 3, 29),  # Good Friday
            datetime(2024, 5, 27),  # Memorial Day
            datetime(2024, 6, 19),  # Juneteenth
            datetime(2024, 7, 4),   # Independence Day
            datetime(2024, 9, 2),   # Labor Day
            datetime(2024, 11, 28), # Thanksgiving
            datetime(2024, 12, 25), # Christmas
        ]
        
        self.market_holidays_2025 = [
            datetime(2025, 1, 1),   # New Year's Day
            datetime(2025, 1, 20),  # Martin Luther King Jr. Day
            datetime(2025, 2, 17),  # Presidents' Day
            datetime(2025, 4, 18),  # Good Friday
            datetime(2025, 5, 26),  # Memorial Day
            datetime(2025, 6, 19),  # Juneteenth
            datetime(2025, 7, 4),   # Independence Day
            datetime(2025, 9, 1),   # Labor Day
            datetime(2025, 11, 27), # Thanksgiving
            datetime(2025, 12, 25), # Christmas
        ]
    
    def get_current_eastern_time(self) -> datetime:
        """Get current time in Eastern timezone"""
        return datetime.now(self.eastern_tz)
    
    def is_market_open_today(self, date: Optional[datetime] = None) -> bool:
        """Check if market is open on given date (default: today)"""
        if date is None:
            date = self.get_current_eastern_time().date()
        else:
            date = date.date() if isinstance(date, datetime) else date
        
        # Check if it's a weekend
        if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if it's a holiday
        date_dt = datetime.combine(date, time())
        if date_dt in self.market_holidays_2024 or date_dt in self.market_holidays_2025:
            return False
        
        return True
    
    def is_market_open_now(self) -> bool:
        """Check if market is currently open"""
        now = self.get_current_eastern_time()
        
        # Check if today is a trading day
        if not self.is_market_open_today(now):
            return False
        
        # Check if current time is within market hours
        current_time = now.time()
        return self.market_open_time <= current_time <= self.market_close_time
    
    def is_pre_market_hours(self) -> bool:
        """Check if currently in pre-market hours"""
        now = self.get_current_eastern_time()
        
        if not self.is_market_open_today(now):
            return False
        
        current_time = now.time()
        return self.pre_market_start <= current_time < self.market_open_time
    
    def is_after_hours(self) -> bool:
        """Check if currently in after-hours trading"""
        now = self.get_current_eastern_time()
        
        if not self.is_market_open_today(now):
            return False
        
        current_time = now.time()
        return self.market_close_time < current_time <= self.after_hours_end
    
    def get_next_market_open(self) -> datetime:
        """Get the next market open datetime"""
        now = self.get_current_eastern_time()
        
        # If market is currently open, return today's open time
        if self.is_market_open_now():
            return now.replace(
                hour=self.market_open_time.hour,
                minute=self.market_open_time.minute,
                second=0,
                microsecond=0
            )
        
        # Start checking from today
        check_date = now.date()
        
        # If it's after market close today, start checking from tomorrow
        if now.time() > self.market_close_time:
            check_date += timedelta(days=1)
        
        # Find next trading day
        while not self.is_market_open_today(check_date):
            check_date += timedelta(days=1)
        
        return self.eastern_tz.localize(
            datetime.combine(check_date, self.market_open_time)
        )
    
    def get_next_market_close(self) -> datetime:
        """Get the next market close datetime"""
        now = self.get_current_eastern_time()
        
        # If market is currently open, return today's close time
        if self.is_market_open_now():
            return now.replace(
                hour=self.market_close_time.hour,
                minute=self.market_close_time.minute,
                second=0,
                microsecond=0
            )
        
        # Find next trading day
        check_date = now.date()
        if now.time() > self.market_close_time:
            check_date += timedelta(days=1)
        
        while not self.is_market_open_today(check_date):
            check_date += timedelta(days=1)
        
        return self.eastern_tz.localize(
            datetime.combine(check_date, self.market_close_time)
        )
    
    def get_trading_days_between(self, start_date: datetime, end_date: datetime) -> int:
        """Get number of trading days between two dates"""
        trading_days = 0
        current_date = start_date.date()
        end_date = end_date.date()
        
        while current_date <= end_date:
            if self.is_market_open_today(current_date):
                trading_days += 1
            current_date += timedelta(days=1)
        
        return trading_days
    
    def get_market_status(self) -> str:
        """Get current market status as string"""
        if self.is_market_open_now():
            return "OPEN"
        elif self.is_pre_market_hours():
            return "PRE_MARKET"
        elif self.is_after_hours():
            return "AFTER_HOURS"
        else:
            return "CLOSED"
    
    def time_until_market_open(self) -> Optional[timedelta]:
        """Get time remaining until market opens"""
        if self.is_market_open_now():
            return timedelta(0)
        
        next_open = self.get_next_market_open()
        now = self.get_current_eastern_time()
        
        return next_open - now
    
    def time_until_market_close(self) -> Optional[timedelta]:
        """Get time remaining until market closes"""
        if not self.is_market_open_now():
            return None
        
        next_close = self.get_next_market_close()
        now = self.get_current_eastern_time()
        
        return next_close - now
    
    def get_market_hours_today(self) -> tuple:
        """Get today's market open and close times"""
        today = self.get_current_eastern_time().date()
        
        if not self.is_market_open_today(today):
            return None, None
        
        market_open = self.eastern_tz.localize(
            datetime.combine(today, self.market_open_time)
        )
        market_close = self.eastern_tz.localize(
            datetime.combine(today, self.market_close_time)
        )
        
        return market_open, market_close
