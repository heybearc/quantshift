#!/usr/bin/env python3
"""
QuantShift Equity Bot Runner with StateManager Integration
This script runs the existing Alpaca trading bot and integrates it with Redis state management
Fetches real account data, positions, and trades from Alpaca API
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# Add the core package to the path
sys.path.insert(0, '/opt/quantshift/packages/core/src')

from quantshift_core.state_manager import StateManager
from quantshift_core.database import get_db
from quantshift_core.models import Trade

# Admin platform integration
from database_writer import DatabaseWriter

# Alpaca SDK
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuantShiftEquityBot:
    def __init__(self):
        self.bot_name = "equity-bot"
        self.state_manager = StateManager(bot_name=self.bot_name)
        self.running = True
        
        # Initialize Alpaca client
        self.alpaca_client = TradingClient(
            api_key=os.getenv('APCA_API_KEY_ID'),
            secret_key=os.getenv('APCA_API_SECRET_KEY'),
            paper=True  # Paper trading mode
        )
        
        # Initialize database writer for admin platform
        self.db_writer = DatabaseWriter(bot_name=self.bot_name)
        try:
            self.db_writer.connect()
            logger.info("Connected to admin platform database")
        except Exception as e:
            logger.warning(f"Could not connect to admin platform database: {e}")
            self.db_writer = None
        
        # Trading cost assumptions for live trading simulation
        self.commission_per_trade = 0.0  # Alpaca has zero commissions
        self.slippage_bps = 5  # 5 basis points (0.05%) slippage estimate
        self.expected_live_capital = 10000.00  # Expected starting capital for live trading
        
        # Track last processed order to avoid duplicates
        self.last_processed_order_id = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        logger.info(f"Initialized {self.bot_name} with Alpaca paper trading")
        logger.info(f"Expected live capital: ${self.expected_live_capital:,.2f}")
        logger.info(f"Estimated slippage: {self.slippage_bps} bps per trade")
        
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.db_writer:
            self.db_writer.disconnect()
        
    def get_account_info(self):
        """Fetch real account information from Alpaca"""
        try:
            account = self.alpaca_client.get_account()
            return {
                'balance': float(account.cash),
                'equity': float(account.equity),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'pattern_day_trader': account.pattern_day_trader,
                'daytrade_count': account.daytrade_count,
                'last_equity': float(account.last_equity)
            }
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            return None
            
    def get_positions(self):
        """Fetch real positions from Alpaca"""
        try:
            positions = self.alpaca_client.get_all_positions()
            position_list = []
            
            for pos in positions:
                position_data = {
                    'symbol': pos.symbol,
                    'quantity': float(pos.qty),
                    'entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price),
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc),
                    'side': pos.side
                }
                position_list.append(position_data)
                
                # Save position to Redis for quick recovery
                self.state_manager.save_position(pos.symbol, position_data)
                
            return position_list
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
            
    def get_total_trades_count(self):
        """Get total number of trades from database"""
        try:
            db = next(get_db())
            count = db.query(Trade).filter(Trade.bot_name == self.bot_name).count()
            db.close()
            return count
        except Exception as e:
            logger.error(f"Error getting trades count: {e}")
            return 0
            
    def sync_trades_to_database(self):
        """Sync recent trades from Alpaca to PostgreSQL"""
        try:
            # Get orders from last 24 hours
            request = GetOrdersRequest(
                status=QueryOrderStatus.FILLED,
                limit=100,
                after=datetime.utcnow() - timedelta(days=1)
            )
            orders = self.alpaca_client.get_orders(filter=request)
            
            db = next(get_db())
            new_trades = 0
            
            for order in orders:
                # Skip if already processed
                if order.id == self.last_processed_order_id:
                    break
                    
                # Calculate realistic costs for live trading
                fill_price = float(order.filled_avg_price) if order.filled_avg_price else float(order.limit_price or 0)
                quantity = float(order.filled_qty)
                
                # Add slippage cost estimate
                slippage_cost = fill_price * quantity * (self.slippage_bps / 10000)
                total_value = fill_price * quantity
                
                # Check if trade already exists
                existing = db.query(Trade).filter(Trade.order_id == order.id).first()
                if existing:
                    continue
                
                # Create trade record
                trade = Trade(
                    bot_name=self.bot_name,
                    symbol=order.symbol,
                    side=order.side.value,
                    quantity=quantity,
                    price=fill_price,
                    total_value=total_value,
                    commission=self.commission_per_trade,
                    order_id=order.id,
                    status=order.status.value,
                    timestamp=order.filled_at or order.created_at,
                    metadata={
                        'order_type': order.type.value,
                        'time_in_force': order.time_in_force.value,
                        'estimated_slippage': slippage_cost,
                        'paper_trading': True
                    }
                )
                
                db.add(trade)
                new_trades += 1
                logger.info(f"Synced trade: {order.side.value} {quantity} {order.symbol} @ ${fill_price:.2f}")
            
            if new_trades > 0:
                db.commit()
                logger.info(f"Synced {new_trades} new trades to database")
                
            # Update last processed order
            if orders:
                self.last_processed_order_id = orders[0].id
                
            db.close()
            return new_trades
            
        except Exception as e:
            logger.error(f"Error syncing trades: {e}", exc_info=True)
            return 0
        
    def update_state(self):
        """Update bot state in Redis with real Alpaca data"""
        try:
            # Get real account info
            account_info = self.get_account_info()
            positions = self.get_positions()
            
            if account_info:
                # Calculate total unrealized P&L
                total_unrealized_pl = sum(p['unrealized_pl'] for p in positions)
                
                state = {
                    'status': 'running',
                    'mode': 'paper',
                    'last_update': datetime.utcnow().isoformat(),
                    'strategy': 'multi-strategy',
                    'account_balance': account_info['balance'],
                    'equity': account_info['equity'],
                    'buying_power': account_info['buying_power'],
                    'portfolio_value': account_info['portfolio_value'],
                    'positions_count': len(positions),
                    'unrealized_pl': total_unrealized_pl,
                    'pattern_day_trader': account_info['pattern_day_trader'],
                    'daytrade_count': account_info['daytrade_count'],
                    'expected_live_capital': self.expected_live_capital,
                    'estimated_slippage_bps': self.slippage_bps
                }
                
                self.state_manager.save_state(state)
                logger.info(f"State updated - Balance: ${account_info['balance']:,.2f}, "
                          f"Positions: {len(positions)}, Unrealized P&L: ${total_unrealized_pl:,.2f}")
                
                # Update admin platform database
                if self.db_writer:
                    try:
                        self.db_writer.update_status(
                            account_info=account_info,
                            positions=positions,
                            trades_count=self.get_total_trades_count()
                        )
                        self.db_writer.update_positions(positions)
                    except Exception as e:
                        logger.error(f"Error updating admin platform: {e}")
            else:
                # Fallback state if API call fails
                state = {
                    'status': 'running',
                    'mode': 'paper',
                    'last_update': datetime.utcnow().isoformat(),
                    'strategy': 'multi-strategy',
                    'account_balance': self.expected_live_capital,
                    'positions_count': 0,
                    'error': 'Failed to fetch account data'
                }
                self.state_manager.save_state(state)
                
        except Exception as e:
            logger.error(f"Error updating state: {e}", exc_info=True)
        
    def send_heartbeat(self):
        """Send heartbeat to Redis"""
        self.state_manager.heartbeat()
        
    def run(self):
        """Main bot loop"""
        logger.info(f"Starting {self.bot_name}...")
        
        # Initial state update and trade sync
        self.update_state()
        self.sync_trades_to_database()
        
        # Main loop intervals
        heartbeat_interval = 30  # seconds
        state_update_interval = 60  # seconds
        trade_sync_interval = 300  # 5 minutes
        last_heartbeat = time.time()
        last_state_update = time.time()
        last_trade_sync = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Send heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat = current_time
                    logger.debug("Heartbeat sent")
                
                # Update state with real Alpaca data
                if current_time - last_state_update >= state_update_interval:
                    self.update_state()
                    last_state_update = current_time
                
                # Sync trades to database
                if current_time - last_trade_sync >= trade_sync_interval:
                    new_trades = self.sync_trades_to_database()
                    last_trade_sync = current_time
                    if new_trades > 0:
                        logger.info(f"Synced {new_trades} new trades")
                
                # Sleep to avoid busy waiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5)
        
        # Cleanup
        if self.db_writer:
            self.db_writer.disconnect()
        logger.info("Bot stopped")

if __name__ == '__main__':
    bot = QuantShiftEquityBot()
    bot.run()
