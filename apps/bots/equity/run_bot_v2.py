#!/usr/bin/env python3
"""
QuantShift Equity Bot V2 - Broker-Agnostic Architecture

This version uses the new broker-agnostic strategy framework:
- Strategies are pure logic (no broker dependencies)
- AlpacaExecutor handles Alpaca-specific execution
- Same strategy code can be used for backtesting and live trading
"""
import os
import sys
import time
import signal
import logging
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the core package to the path
sys.path.insert(0, '/opt/quantshift/packages/core/src')

from quantshift_core.state_manager import StateManager
from quantshift_core.database import get_db
from quantshift_core.models import Trade
from quantshift_core.strategies import MACrossoverStrategy

# Admin platform integration
from database_writer import DatabaseWriter

# Alpaca SDK
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient

# Import our Alpaca executor
from alpaca_executor import AlpacaExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuantShiftEquityBotV2:
    """
    Equity trading bot using broker-agnostic strategy architecture.
    """
    
    def __init__(self, config_path: str = '/opt/quantshift/config/equity_strategy.yaml'):
        """Initialize the bot with configuration."""
        self.bot_name = "equity-bot"
        self.state_manager = StateManager(bot_name=self.bot_name)
        self.running = True
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize Alpaca clients
        self.alpaca_client = TradingClient(
            api_key=os.getenv('APCA_API_KEY_ID'),
            secret_key=os.getenv('APCA_API_SECRET_KEY'),
            paper=True  # Paper trading mode
        )
        
        self.data_client = StockHistoricalDataClient(
            api_key=os.getenv('APCA_API_KEY_ID'),
            secret_key=os.getenv('APCA_API_SECRET_KEY')
        )
        
        # Initialize strategy (broker-agnostic)
        strategy_config = self.config.get('strategy', {}).get('parameters', {})
        strategy_config.update(self.config.get('risk_management', {}))
        strategy_config.update(self.config.get('filters', {}))
        
        self.strategy = MACrossoverStrategy(config=strategy_config)
        
        # Initialize Alpaca executor
        symbols = self.config.get('strategy', {}).get('symbols', ['SPY'])
        
        self.executor = AlpacaExecutor(
            strategy=self.strategy,
            alpaca_client=self.alpaca_client,
            data_client=self.data_client,
            symbols=symbols,
            simulated_capital=None  # Use real Alpaca account equity
        )
        
        # Trading cost assumptions
        self.commission_per_trade = 0.0
        self.slippage_bps = self.config.get('execution', {}).get('costs', {}).get('slippage_bps', 5)
        
        # Track last processed order
        self.last_processed_order_id = None
        
        # Initialize database writer for admin platform heartbeats
        self.db_writer = DatabaseWriter(bot_name=self.bot_name)
        try:
            self.db_writer.connect()
            logger.info("Connected to admin platform database")
        except Exception as e:
            logger.warning(f"Could not connect to admin platform database: {e}")
            self.db_writer = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        logger.info(f"Initialized {self.bot_name} V2 with broker-agnostic architecture")
        logger.info(f"Strategy: {self.strategy.name}")
        logger.info(f"Symbols: {symbols}")
        logger.info(f"Paper Trading: Enabled")
        
        # Seed bot_config table so dashboard shows strategy name
        self._seed_bot_config()
    
    def _seed_bot_config(self):
        """Ensure bot_config table has an entry so dashboard shows strategy name."""
        if not self.db_writer:
            return
        try:
            cursor = self.db_writer.conn.cursor()
            symbols = self.config.get('strategy', {}).get('symbols', ['SPY', 'QQQ'])
            import uuid as _uuid
            cursor.execute("""
                INSERT INTO bot_config (
                    id, name, strategy, symbols, enabled, paper_trading,
                    risk_per_trade, max_position_size, max_portfolio_heat,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (name) DO UPDATE SET
                    strategy = EXCLUDED.strategy,
                    updated_at = NOW()
            """, (
                str(_uuid.uuid4()),
                self.bot_name,
                self.strategy.name,
                symbols,
                True,
                True,
                self.config.get('risk_management', {}).get('risk_per_trade', 0.01),
                self.config.get('risk_management', {}).get('max_position_size', 0.20),
                self.config.get('risk_management', {}).get('max_portfolio_heat', 0.10),
            ))
            self.db_writer.conn.commit()
            logger.info(f"Bot config seeded: strategy={self.strategy.name}")
        except Exception as e:
            logger.warning(f"Could not seed bot_config: {e}")
            try:
                self.db_writer.conn.rollback()
            except Exception:
                pass

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            logger.info("Using default configuration")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """Get default configuration if file not found."""
        return {
            'strategy': {
                'name': 'MA Crossover',
                'parameters': {
                    'short_window': 20,
                    'long_window': 50,
                    'atr_period': 14,
                    'risk_per_trade': 0.02
                },
                'symbols': ['SPY', 'QQQ']
            },
            'risk_management': {
                'max_positions': 5,
                'max_portfolio_heat': 0.10
            },
            'execution': {
                'costs': {
                    'slippage_bps': 5
                }
            }
        }
    
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.db_writer:
            self.db_writer.disconnect()
    
    def _ensure_db_connection(self):
        """Ensure db_writer connection is alive, reconnect if needed."""
        if not self.db_writer:
            return False
        try:
            # Test connection with a simple query
            cursor = self.db_writer.conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            return True
        except Exception:
            try:
                self.db_writer.connect()
                return True
            except Exception as e:
                logger.warning(f"Could not reconnect to database: {e}")
                return False

    def sync_trades_to_database(self):
        """Sync recent trades from Alpaca to PostgreSQL via db_writer connection."""
        if not self.db_writer or not self._ensure_db_connection():
            return 0
        try:
            # Get orders from last 24 hours
            request = GetOrdersRequest(
                status=QueryOrderStatus.CLOSED,
                limit=100,
                after=datetime.now(timezone.utc) - timedelta(days=1)
            )
            orders = self.alpaca_client.get_orders(filter=request)
            
            new_trades = 0
            cursor = self.db_writer.conn.cursor()
            
            for order in orders:
                # Skip if already processed
                if order.id == self.last_processed_order_id:
                    break
                
                # Only sync filled orders
                if not order.filled_avg_price or not order.filled_qty:
                    continue
                
                # Check if trade already exists (no order_id col, use symbol+entered_at)
                cursor.execute(
                    'SELECT id FROM trades WHERE bot_name = %s AND symbol = %s AND entered_at = %s',
                    (self.bot_name, order.symbol, order.filled_at or order.created_at)
                )
                if cursor.fetchone():
                    continue
                
                fill_price = float(order.filled_avg_price)
                quantity = float(order.filled_qty)
                
                cursor.execute("""
                    INSERT INTO trades (
                        bot_name, symbol, side, quantity, entry_price,
                        status, strategy, entered_at, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (
                    self.bot_name,
                    order.symbol,
                    order.side.value.upper(),
                    quantity,
                    fill_price,
                    'CLOSED',
                    self.strategy.name,
                    order.filled_at or order.created_at,
                ))
                new_trades += 1
                logger.info(f"Synced trade: {order.side.value} {quantity} {order.symbol} @ ${fill_price:.2f}")
            
            if new_trades > 0:
                self.db_writer.conn.commit()
                logger.info(f"Synced {new_trades} new trades to database")
            
            # Update last processed order
            if orders:
                self.last_processed_order_id = orders[0].id
            
            return new_trades
            
        except Exception as e:
            logger.error(f"Error syncing trades: {e}", exc_info=True)
            try:
                self.db_writer.conn.rollback()
            except Exception:
                pass
            return 0
    
    def update_state(self):
        """Update bot state in Redis."""
        try:
            # Get account and positions
            account = self.executor.get_account()
            positions = self.executor.get_positions()
            
            # Calculate total unrealized P&L
            total_unrealized_pl = sum(p.unrealized_pl for p in positions)
            
            state = {
                'status': 'running',
                'mode': 'paper',
                'last_update': datetime.now(timezone.utc).isoformat(),
                'strategy': self.strategy.name,
                'strategy_config': self.strategy.config,
                'account_balance': account.cash,
                'equity': account.equity,
                'buying_power': account.buying_power,
                'portfolio_value': account.portfolio_value,
                'positions_count': len(positions),
                'unrealized_pl': total_unrealized_pl,
                'symbols': self.config.get('strategy', {}).get('symbols', []),
                'architecture': 'broker_agnostic_v2'
            }
            
            self.state_manager.save_state(state)
            
            # Save individual positions
            for pos in positions:
                self.state_manager.save_position(pos.symbol, pos.to_dict())
            
            logger.info(
                f"State updated - Balance: ${account.cash:.2f}, "
                f"Equity: ${account.equity:.2f}, "
                f"Positions: {len(positions)}, "
                f"Unrealized P&L: ${total_unrealized_pl:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Error updating state: {e}", exc_info=True)
    
    def send_heartbeat(self):
        """Send heartbeat to Redis and PostgreSQL bot_status table."""
        self.state_manager.heartbeat()
        
        # Also write to DB so the dashboard shows RUNNING
        if self.db_writer and self._ensure_db_connection():
            try:
                account = self.executor.get_account()
                positions = self.executor.get_positions()
                trades_count = 0
                try:
                    cursor = self.db_writer.conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM trades WHERE bot_name = %s', (self.bot_name,))
                    trades_count = cursor.fetchone()[0]
                except Exception:
                    pass
                pos_dicts = [p.to_dict() for p in positions]
                self.db_writer.update_status(
                    account_info={
                        'equity': account.equity,
                        'balance': account.cash,
                        'buying_power': account.buying_power,
                        'portfolio_value': account.portfolio_value,
                    },
                    positions=pos_dicts,
                    trades_count=trades_count
                )
                # Sync live positions to positions table
                if pos_dicts:
                    self.db_writer.update_positions(pos_dicts)
            except Exception as e:
                logger.warning(f"Could not write DB heartbeat: {e}", exc_info=True)
    
    def run_strategy(self):
        """Run strategy cycle to generate and execute signals."""
        try:
            # Check if strategy is enabled
            if not self.config.get('strategy', {}).get('enabled', True):
                logger.debug("Strategy execution disabled in config")
                return
            
            # Check if paper trading is enabled
            if not self.config.get('paper_trading', {}).get('enabled', True):
                logger.debug("Paper trading disabled in config")
                return
            
            logger.info("Running strategy cycle...")
            
            results = self.executor.run_strategy_cycle()
            
            # Log results
            logger.info(
                f"Strategy cycle completed - "
                f"Symbols checked: {len(results['symbols_checked'])}, "
                f"Signals generated: {len(results['signals_generated'])}, "
                f"Orders executed: {len(results['orders_executed'])}"
            )
            
            if results['errors']:
                logger.warning(f"Errors during cycle: {results['errors']}")
            
            # Log signals
            for signal in results['signals_generated']:
                logger.info(
                    f"Signal: {signal['type']} {signal['symbol']} @ ${signal['price']:.2f} - {signal['reason']}"
                )

            # Record executed orders to trades table
            if results['orders_executed'] and self.db_writer and self._ensure_db_connection():
                for order in results['orders_executed']:
                    try:
                        side = order.get('side', 'BUY')
                        symbol = order.get('symbol', '')
                        qty = order.get('quantity', order.get('qty', 0))
                        price = order.get('fill_price', order.get('price', 0))
                        reason = order.get('reason', '')
                        if side.upper() in ('BUY', 'LONG') and symbol and price:
                            self.db_writer.record_trade_entry(
                                symbol=symbol,
                                side='BUY',
                                quantity=float(qty),
                                entry_price=float(price),
                                strategy=self.strategy.name,
                                signal_type='buy_signal',
                                entry_reason=reason,
                            )
                        elif side.upper() in ('SELL', 'SHORT') and symbol and price:
                            self.db_writer.record_trade_entry(
                                symbol=symbol,
                                side='SELL',
                                quantity=float(qty),
                                entry_price=float(price),
                                strategy=self.strategy.name,
                                signal_type='sell_signal',
                                entry_reason=reason,
                            )
                    except Exception as te:
                        logger.warning(f"Could not record trade to DB: {te}")

        except Exception as e:
            logger.error(f"Error in strategy execution: {e}", exc_info=True)
    
    def run(self):
        """Main bot loop."""
        logger.info(f"Starting {self.bot_name} V2...")
        
        # Initial updates
        self.update_state()
        self.sync_trades_to_database()
        
        # Main loop intervals
        heartbeat_interval = 30  # seconds
        state_update_interval = 60  # seconds
        trade_sync_interval = 300  # 5 minutes
        strategy_interval = self.config.get('strategy', {}).get('schedule', {}).get('check_interval', 300)  # 5 minutes
        
        last_heartbeat = time.time()
        last_state_update = time.time()
        last_trade_sync = time.time()
        last_strategy_run = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Send heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat = current_time
                
                # Update state
                if current_time - last_state_update >= state_update_interval:
                    self.update_state()
                    last_state_update = current_time
                
                # Sync trades
                if current_time - last_trade_sync >= trade_sync_interval:
                    self.sync_trades_to_database()
                    last_trade_sync = current_time
                
                # Run strategy
                if current_time - last_strategy_run >= strategy_interval:
                    self.run_strategy()
                    last_strategy_run = current_time
                
                # Sleep to avoid busy waiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5)
        
        logger.info("Bot stopped")


if __name__ == '__main__':
    bot = QuantShiftEquityBotV2()
    bot.run()
