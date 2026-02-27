#!/usr/bin/env python3
"""
QuantShift Unified Trading Bot V3

Universal bot runner that works with any asset class (equity, crypto, forex, etc.)
Uses config-driven executor selection and broker-agnostic strategies.

Architecture:
- Strategies: Asset-agnostic (work on any OHLCV data)
- Executors: Broker-specific (Alpaca, Coinbase, etc.)
- Orchestrator: Manages strategies, regime detection, risk management
- Config: Determines which executor and symbols to use

Usage:
    python run_bot_v3.py --config config/equity_config.yaml
    python run_bot_v3.py --config config/crypto_config.yaml
"""

import os
import sys
import time
import signal
import argparse
import yaml
from datetime import datetime
from typing import Dict, Any, Optional

# Systemd watchdog support
try:
    from systemd import daemon
    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False

# Add packages to path
sys.path.insert(0, '/opt/quantshift/packages/core/src')

import structlog

from quantshift_core.strategies.bollinger_bounce import BollingerBounce
from quantshift_core.strategies.rsi_mean_reversion import RSIMeanReversion
from quantshift_core.strategies.breakout_momentum import BreakoutMomentum
from quantshift_core.strategy_orchestrator import StrategyOrchestrator
from quantshift_core.executors import AlpacaExecutor, CoinbaseExecutor
from quantshift_core.state_manager import StateManager
from quantshift_core.metrics import BotMetrics
from quantshift_core.strategy_performance_tracker import StrategyPerformanceTracker

import psycopg2

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


class QuantShiftUnifiedBot:
    """
    Unified trading bot that works with any asset class.
    
    Config-driven design allows running the same bot code with different:
    - Brokers (Alpaca, Coinbase, Interactive Brokers, etc.)
    - Asset classes (equity, crypto, forex, commodities)
    - Strategies (any combination of available strategies)
    - Symbols (any tradeable instruments)
    """
    
    def __init__(self, config_path: str):
        """
        Initialize unified bot from config file.
        
        Args:
            config_path: Path to YAML config file
        """
        self.config = self._load_config(config_path)
        self.running = False
        self.state_manager = None
        self.executor = None
        self.db_conn = None
        self.performance_tracker = None
        self.bot_name = self.config.get('bot_name', 'quantshift-bot')
        self.recovered_positions = {}
        
        logger.info(
            "bot_initializing",
            bot_type=self.config.get('bot_type', 'unknown'),
            version="3.0"
        )
        
        # Initialize Prometheus metrics
        metrics_port = self.config.get('metrics_port', 9100)
        self.metrics = BotMetrics(
            component_name=self.bot_name.replace('-', '_'),
            port=metrics_port
        )
        self.metrics.set_info(version="3.0", environment="production")
        self.metrics.start_server()
        
        # Initialize components
        self._init_state_manager()
        self._init_strategies()
        self._init_executor()
        
        # Recover positions from Redis (for failover/restart)
        self._recover_positions()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("bot_initialized", config=config_path)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info("config_loaded", path=config_path)
            return config
        except Exception as e:
            logger.error("config_load_failed", path=config_path, error=str(e))
            raise
    
    def _init_state_manager(self):
        """Initialize Redis state manager."""
        try:
            self.state_manager = StateManager(
                bot_name=self.config.get('bot_name', 'quantshift-bot')
            )
            logger.info("state_manager_initialized")
        except Exception as e:
            logger.error("state_manager_init_failed", error=str(e))
            raise
    
    def _init_strategies(self):
        """Initialize trading strategies from config."""
        strategy_configs = self.config.get('strategies', [])
        
        if not strategy_configs:
            raise ValueError("No strategies configured")
        
        self.strategies = []
        
        for strat_config in strategy_configs:
            strategy_type = strat_config.get('type')
            strategy_params = strat_config.get('params', {})
            
            if strategy_type == 'BollingerBounce':
                strategy = BollingerBounce(config=strategy_params)
            elif strategy_type == 'RSIMeanReversion':
                strategy = RSIMeanReversion(config=strategy_params)
            elif strategy_type == 'BreakoutMomentum':
                strategy = BreakoutMomentum(config=strategy_params)
            else:
                logger.warning("unknown_strategy_type", type=strategy_type)
                continue
            
            self.strategies.append(strategy)
            logger.info("strategy_loaded", type=strategy_type, name=strategy.name)
        
        # Create orchestrator
        orchestrator_config = self.config.get('orchestrator', {})
        capital_allocation = orchestrator_config.get('capital_allocation')
        use_regime_detection = orchestrator_config.get('use_regime_detection', True)
        use_ml_regime = orchestrator_config.get('use_ml_regime', False)
        use_risk_management = orchestrator_config.get('use_risk_management', True)
        use_sentiment_analysis = orchestrator_config.get('use_sentiment_analysis', False)
        
        self.strategy = StrategyOrchestrator(
            strategies=self.strategies,
            capital_allocation=capital_allocation,
            use_regime_detection=use_regime_detection,
            use_ml_regime=use_ml_regime,
            use_risk_management=use_risk_management,
            use_sentiment_analysis=use_sentiment_analysis
        )
        
        logger.info(
            "orchestrator_initialized",
            num_strategies=len(self.strategies),
            regime_detection=use_regime_detection,
            ml_regime=use_ml_regime,
            risk_management=use_risk_management,
            sentiment_analysis=use_sentiment_analysis
        )
    
    def _init_executor(self):
        """Initialize broker-specific executor from config."""
        executor_config = self.config.get('executor', {})
        executor_type = executor_config.get('type')
        
        if executor_type == 'alpaca':
            self._init_alpaca_executor(executor_config)
        elif executor_type == 'coinbase':
            self._init_coinbase_executor(executor_config)
        else:
            raise ValueError(f"Unknown executor type: {executor_type}")
    
    def _init_alpaca_executor(self, config: Dict[str, Any]):
        """Initialize Alpaca executor for equity trading."""
        from alpaca.trading.client import TradingClient
        from alpaca.data.historical import StockHistoricalDataClient
        
        # Get API credentials from environment
        api_key = os.getenv('APCA_API_KEY_ID')
        secret_key = os.getenv('APCA_API_SECRET_KEY')
        paper = config.get('paper', True)
        
        if not api_key or not secret_key:
            raise ValueError("Alpaca API credentials not found in environment")
        
        # Initialize clients
        alpaca_client = TradingClient(api_key, secret_key, paper=paper)
        data_client = StockHistoricalDataClient(api_key, secret_key)
        
        # Get symbols and risk config
        use_dynamic_symbols = config.get('use_dynamic_symbols', False)
        symbol_universe_config = config.get('symbol_universe')
        symbols = config.get('symbols', ['SPY']) if not use_dynamic_symbols else None
        simulated_capital = config.get('simulated_capital')
        risk_config = self.config.get('risk_management', {})
        
        self.executor = AlpacaExecutor(
            strategy=self.strategy,
            alpaca_client=alpaca_client,
            data_client=data_client,
            symbols=symbols,
            simulated_capital=simulated_capital,
            risk_config=risk_config,
            use_dynamic_symbols=use_dynamic_symbols,
            symbol_universe_config=symbol_universe_config
        )
        
        logger.info(
            "alpaca_executor_initialized",
            paper=paper,
            use_dynamic_symbols=use_dynamic_symbols,
            symbol_count=len(self.executor.symbols) if self.executor.symbols else "lazy_loading",
            simulated_capital=simulated_capital
        )
    
    def _init_coinbase_executor(self, config: Dict[str, Any]):
        """Initialize Coinbase executor for crypto trading."""
        from coinbase.rest import RESTClient
        
        # Get API credentials from environment (support both old and new CDP SDK)
        api_key = os.getenv('COINBASE_API_KEY')
        api_secret = os.getenv('COINBASE_API_SECRET')
        cdp_key_name = os.getenv('CDP_API_KEY_NAME')
        cdp_private_key = os.getenv('CDP_API_KEY_PRIVATE_KEY')
        
        # Use CDP credentials if available, otherwise fall back to legacy
        if cdp_key_name and cdp_private_key:
            logger.info("using_cdp_sdk_credentials")
            coinbase_client = RESTClient(api_key=cdp_key_name, api_secret=cdp_private_key)
        elif api_key and api_secret:
            logger.info("using_legacy_coinbase_credentials")
            coinbase_client = RESTClient(api_key=api_key, api_secret=api_secret)
        else:
            raise ValueError("Coinbase API credentials not found in environment (need either COINBASE_API_KEY/SECRET or CDP_API_KEY_NAME/PRIVATE_KEY)")
        
        # Initialize client (already done above)
        
        # Get symbols and risk config
        use_dynamic_symbols = config.get('use_dynamic_symbols', False)
        symbol_universe_config = config.get('symbol_universe')
        symbols = config.get('symbols', ['BTC-USD']) if not use_dynamic_symbols else None
        simulated_capital = config.get('simulated_capital', 10000)
        risk_config = self.config.get('risk_management', {})
        
        self.executor = CoinbaseExecutor(
            strategy=self.strategy,
            coinbase_client=coinbase_client,
            symbols=symbols,
            simulated_capital=simulated_capital,
            risk_config=risk_config,
            use_dynamic_symbols=use_dynamic_symbols,
            symbol_universe_config=symbol_universe_config
        )
        
        logger.info(
            "coinbase_executor_initialized",
            use_dynamic_symbols=use_dynamic_symbols,
            symbol_count=len(self.executor.symbols) if self.executor.symbols else "lazy_loading",
            simulated_capital=simulated_capital
        )
    
    def _recover_positions(self):
        """
        Recover positions from Redis on startup.
        
        This enables:
        1. Bot restart without losing position tracking
        2. Standby failover with full position context
        3. Reconciliation with broker API to handle discrepancies
        4. Risk validation to prevent over-leverage
        """
        try:
            # Load positions from Redis
            redis_positions = self.state_manager.load_positions()
            
            if not redis_positions:
                logger.info("position_recovery_none", message="No positions to recover")
                return
            
            logger.info("position_recovery_started", count=len(redis_positions))
            
            # Get current positions from broker
            try:
                broker_positions = self.executor.get_positions()
                broker_symbols = {pos.symbol for pos in broker_positions}
            except Exception as e:
                logger.warning("broker_positions_fetch_failed", error=str(e))
                broker_symbols = set()
            
            # Get account equity for risk validation
            try:
                account_info = self.executor.get_account()
                account_equity = float(account_info.equity) if hasattr(account_info, 'equity') else float(account_info.get('equity', 0))
            except Exception as e:
                logger.warning("account_equity_fetch_failed", error=str(e))
                account_equity = 0
            
            # Reconcile positions and validate risk
            recovered_count = 0
            discrepancy_count = 0
            total_position_value = 0.0
            
            for symbol, redis_data in redis_positions.items():
                if symbol in broker_symbols:
                    # Position exists in both Redis and broker - recovered successfully
                    self.recovered_positions[symbol] = redis_data
                    recovered_count += 1
                    
                    # Calculate position value
                    quantity = float(redis_data.get('quantity', 0))
                    current_price = float(redis_data.get('current_price', redis_data.get('entry_price', 0)))
                    position_value = abs(quantity * current_price)
                    total_position_value += position_value
                    
                    logger.info(
                        "position_recovered",
                        symbol=symbol,
                        quantity=redis_data.get('quantity'),
                        entry_price=redis_data.get('entry_price'),
                        position_value=position_value
                    )
                else:
                    # Position in Redis but not in broker - likely closed
                    discrepancy_count += 1
                    logger.warning(
                        "position_discrepancy",
                        symbol=symbol,
                        status="closed_at_broker",
                        action="clearing_redis"
                    )
                    # Clear stale position from Redis
                    self.state_manager.clear_position(symbol)
            
            # Validate recovered positions against risk limits
            if account_equity > 0:
                leverage_ratio = total_position_value / account_equity
                max_leverage = 1.0  # Cash account should not exceed 1.0x
                
                if leverage_ratio > max_leverage:
                    logger.warning(
                        "position_recovery_over_leveraged",
                        total_position_value=total_position_value,
                        account_equity=account_equity,
                        leverage_ratio=round(leverage_ratio, 2),
                        max_leverage=max_leverage,
                        action="positions_recovered_but_trading_restricted"
                    )
                    # Note: Positions are recovered but orchestrator should not open new positions
                    # until leverage is reduced through natural position closes
                else:
                    logger.info(
                        "position_recovery_risk_validated",
                        total_position_value=total_position_value,
                        account_equity=account_equity,
                        leverage_ratio=round(leverage_ratio, 2)
                    )
            
            logger.info(
                "position_recovery_complete",
                recovered=recovered_count,
                discrepancies=discrepancy_count,
                total=len(redis_positions),
                total_position_value=round(total_position_value, 2)
            )
            
        except Exception as e:
            logger.error("position_recovery_failed", error=str(e), exc_info=True)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("shutdown_signal_received", signal=signum)
        self.running = False
        
        # Save positions to Redis before shutdown
        self._save_positions_on_shutdown()
    
    def _save_positions_on_shutdown(self):
        """Save all open positions to Redis before shutdown for recovery."""
        try:
            positions = self.executor.get_positions()
            
            if not positions:
                logger.info("shutdown_no_positions_to_save")
                return
            
            logger.info("shutdown_saving_positions", count=len(positions))
            
            for pos in positions:
                position_data = {
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pl': pos.unrealized_pl,
                    'saved_at': datetime.utcnow().isoformat()
                }
                
                # Save to Redis
                self.state_manager.save_position(pos.symbol, position_data)
                
                logger.info(
                    "shutdown_position_saved",
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    entry_price=pos.entry_price
                )
            
            logger.info("shutdown_positions_saved", count=len(positions))
            
        except Exception as e:
            logger.error("shutdown_position_save_failed", error=str(e), exc_info=True)
    
    def update_state(self):
        """Update bot state in Redis and database."""
        try:
            # Get account and positions from executor
            account = self.executor.get_account()
            positions = self.executor.get_positions()
            
            # Save positions to Redis for recovery
            for pos in positions:
                position_data = {
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pl': pos.unrealized_pl,
                    'updated_at': datetime.utcnow().isoformat()
                }
                self.state_manager.save_position(pos.symbol, position_data)
            
            # Update state manager
            state = {
                'equity': account.equity,
                'cash': account.cash,
                'buying_power': account.buying_power,
                'positions_count': len(positions),
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'quantity': pos.quantity,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'unrealized_pl': pos.unrealized_pl
                    }
                    for pos in positions
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.state_manager.update_state(state)
            
        except Exception as e:
            logger.error("state_update_failed", error=str(e), exc_info=True)
    
    def send_heartbeat(self):
        """Send heartbeat to Redis and PostgreSQL."""
        # Record Prometheus heartbeat
        self.metrics.record_heartbeat()
        
        # Notify systemd watchdog
        if SYSTEMD_AVAILABLE:
            daemon.notify('WATCHDOG=1')
            self.metrics.record_watchdog_notification()
        
        # Send to Redis (don't let failure block DB heartbeat)
        try:
            self.state_manager.heartbeat()
        except Exception as e:
            logger.error("redis_heartbeat_failed", error=str(e))
        
        # Always write to PostgreSQL so dashboard shows correct status
        try:
            self._update_db_heartbeat()
        except Exception as e:
            logger.error("db_heartbeat_failed", error=str(e))
    
    def _update_db_heartbeat(self):
        """Update bot status in PostgreSQL database."""
        try:
            logger.debug("db_heartbeat_starting", bot_name=self.bot_name)
            if not self.db_conn:
                # Get database URL from environment
                db_url = os.getenv('DATABASE_URL', 'postgresql://quantshift:Cloudy_92!@10.92.3.21:5432/quantshift')
                self.db_conn = psycopg2.connect(db_url)
                logger.debug("db_connection_established")
                
                # Initialize performance tracker with database connection
                if not self.performance_tracker:
                    self.performance_tracker = StrategyPerformanceTracker(self.db_conn)
                    logger.info("performance_tracker_initialized")
            
            # Get current account info
            account = self.executor.get_account()
            positions = self.executor.get_positions()
            logger.debug("account_info_retrieved", equity=account.equity)
            
            # Calculate total unrealized P&L from positions
            total_unrealized_pl = sum(float(pos.unrealized_pl) for pos in positions)
            
            # Log P&L calculation for debugging
            logger.info(
                "pnl_calculation",
                bot_name=self.bot_name,
                positions_count=len(positions),
                total_unrealized_pl=total_unrealized_pl,
                account_equity=float(account.equity),
                account_unrealized_pl=float(account.unrealized_pl) if hasattr(account, 'unrealized_pl') else None
            )
            
            # Update Prometheus metrics
            self.metrics.set_portfolio_value(float(account.equity), self.bot_name)
            self.metrics.set_positions_open(len(positions), self.bot_name)
            self.metrics.set_daily_pnl(total_unrealized_pl, self.bot_name)
            
            # Determine bot status based on primary/standby role
            is_primary = self.state_manager.is_primary()
            bot_status = 'PRIMARY' if is_primary else 'STANDBY'
            logger.debug("db_heartbeat_status_check", is_primary=is_primary, bot_status=bot_status, bot_name=self.bot_name)
            
            # Update bot_status table (use UPDATE instead of INSERT to avoid id conflict)
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE bot_status SET
                    status = %s,
                    last_heartbeat = NOW(),
                    account_equity = %s,
                    account_cash = %s,
                    buying_power = %s,
                    portfolio_value = %s,
                    unrealized_pl = %s,
                    realized_pl = %s,
                    positions_count = %s,
                    updated_at = NOW()
                WHERE bot_name = %s
            """, (
                bot_status,
                float(account.equity),
                float(account.cash),
                float(account.buying_power),
                float(account.portfolio_value),
                total_unrealized_pl,
                float(account.realized_pl) if hasattr(account, 'realized_pl') else 0.0,
                len(positions),
                self.bot_name
            ))
            rows_updated = cursor.rowcount
            self.db_conn.commit()
            logger.debug("db_heartbeat_updated", bot_name=self.bot_name, status_set=bot_status, rows_updated=rows_updated)
            
            # Sync positions to database for web dashboard
            self._sync_positions_to_db(positions)
            
        except Exception as e:
            logger.error("db_heartbeat_failed", error=str(e), exc_info=True)
            # Reconnect on next attempt
            if self.db_conn:
                try:
                    self.db_conn.close()
                except:
                    pass
                self.db_conn = None
    
    def _sync_positions_to_db(self, positions: List[Any]) -> None:
        """Sync current positions to database for web dashboard."""
        try:
            if not self.db_conn:
                return
            
            cursor = self.db_conn.cursor()
            
            # Get currently held symbols
            current_symbols = [pos.symbol for pos in positions] if positions else []
            
            # Find positions that were closed (in DB but not in current positions)
            if self.performance_tracker:
                cursor.execute("""
                    SELECT symbol, unrealized_pl, entry_price, current_price, strategy
                    FROM positions 
                    WHERE bot_name = %s AND (symbol != ALL(%s) OR %s = 0)
                """, (self.bot_name, current_symbols if current_symbols else [''], len(current_symbols)))
                
                closed_positions = cursor.fetchall()
                
                # Update strategy performance for each closed position
                for symbol, unrealized_pl, entry_price, current_price, strategy_name in closed_positions:
                    if unrealized_pl is not None and entry_price and current_price:
                        # Calculate P&L percentage
                        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                        is_win = unrealized_pl > 0
                        
                        # Update strategy performance
                        self.performance_tracker.update_strategy_performance(
                            bot_name=self.bot_name,
                            strategy_name=strategy_name or 'StrategyOrchestrator',
                            trade_pnl=float(unrealized_pl),
                            trade_pnl_pct=pnl_pct,
                            is_win=is_win
                        )
                        
                        logger.info(
                            "strategy_performance_updated",
                            symbol=symbol,
                            strategy=strategy_name,
                            pnl=unrealized_pl,
                            pnl_pct=pnl_pct,
                            is_win=is_win
                        )
            
            # Delete positions no longer held
            if current_symbols:
                cursor.execute("""
                    DELETE FROM positions 
                    WHERE bot_name = %s AND symbol != ALL(%s)
                """, (self.bot_name, current_symbols))
            else:
                # No positions held, delete all
                cursor.execute("""
                    DELETE FROM positions 
                    WHERE bot_name = %s
                """, (self.bot_name,))
            
            # Upsert each position
            for pos in positions:
                # Generate deterministic ID from bot_name and symbol
                position_id = f"{self.bot_name}_{pos.symbol}"
                
                # Get strategy name from Redis (stored when signal was executed)
                strategy_name = 'StrategyOrchestrator'  # Default
                try:
                    redis_key = f"bot:{self.bot_name}:position:{pos.symbol}"
                    position_data = self.state_manager.redis_client.get(redis_key)
                    if position_data:
                        import json
                        pos_dict = json.loads(position_data)
                        strategy_name = pos_dict.get('strategy', 'StrategyOrchestrator')
                except Exception as e:
                    logger.debug("strategy_attribution_lookup_failed", symbol=pos.symbol, error=str(e))
                
                cursor.execute("""
                    INSERT INTO positions (
                        id, bot_name, symbol, quantity, entry_price, current_price,
                        market_value, cost_basis, unrealized_pl, unrealized_pl_pct,
                        strategy, entered_at, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
                    ON CONFLICT (bot_name, symbol) DO UPDATE SET
                        quantity = EXCLUDED.quantity,
                        current_price = EXCLUDED.current_price,
                        market_value = EXCLUDED.market_value,
                        unrealized_pl = EXCLUDED.unrealized_pl,
                        unrealized_pl_pct = EXCLUDED.unrealized_pl_pct,
                        updated_at = NOW()
                """, (
                    position_id,
                    self.bot_name,
                    pos.symbol,
                    float(pos.quantity),
                    float(pos.entry_price),
                    float(pos.current_price),
                    float(pos.market_value),
                    float(pos.cost_basis) if hasattr(pos, 'cost_basis') else float(pos.market_value),
                    float(pos.unrealized_pl),
                    float(pos.unrealized_pl / pos.cost_basis * 100) if hasattr(pos, 'cost_basis') and pos.cost_basis > 0 else 0.0,
                    strategy_name
                ))
            
            self.db_conn.commit()
            logger.debug("positions_synced_to_db", count=len(positions))
            
        except Exception as e:
            logger.error("position_sync_failed", error=str(e), exc_info=True)
            if self.db_conn:
                try:
                    self.db_conn.rollback()
                except:
                    pass
    
    def run(self):
        """Main bot loop with hot-standby failover support."""
        self.running = True
        
        cycle_interval = self.config.get('cycle_interval_seconds', 60)
        heartbeat_interval = self.config.get('heartbeat_interval_seconds', 30)
        
        last_cycle_time = 0
        last_heartbeat_time = 0
        last_primary_check = 0
        is_primary = False
        
        logger.info(
            "bot_started",
            cycle_interval=cycle_interval,
            heartbeat_interval=heartbeat_interval
        )
        
        # Notify systemd that we're ready
        if SYSTEMD_AVAILABLE:
            daemon.notify('READY=1')
            logger.info("systemd_ready_notification_sent")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if this instance should be primary
                # Only check every 5 seconds to avoid rapid switching
                if current_time - last_primary_check >= 5:
                    try:
                        was_primary = is_primary
                        is_primary = self.state_manager.is_primary()
                        last_primary_check = current_time
                        
                        if is_primary and not was_primary:
                            logger.info("became_primary", bot_name=self.bot_name)
                            # Load state from Redis when becoming primary
                            state = self.state_manager.load_state()
                            if state:
                                logger.info("state_loaded_from_redis", keys=list(state.keys()))
                        elif not is_primary and was_primary:
                            logger.info("became_standby", bot_name=self.bot_name)
                    except Exception as e:
                        logger.error("primary_check_failed", error=str(e))
                        # Default to primary if check fails to avoid downtime
                        is_primary = True
                
                # Send heartbeat (only if primary)
                if is_primary and current_time - last_heartbeat_time >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat_time = current_time
                
                # Run strategy cycle (only if primary)
                if is_primary and current_time - last_cycle_time >= cycle_interval:
                    # Check if market is open (for equity) or always run (for crypto)
                    if self.executor.is_market_open():
                        logger.info("strategy_cycle_starting")
                        
                        # Time the cycle for metrics
                        cycle_start = time.time()
                        
                        try:
                            # Run strategy cycle via executor
                            executed_orders = self.executor.run_strategy_cycle()
                            
                            # Update state after cycle
                            self.update_state()
                            
                            # Record cycle duration
                            cycle_duration = time.time() - cycle_start
                            self.metrics.record_cycle_duration(cycle_duration)
                            
                            # Record symbols loaded
                            if hasattr(self.executor, 'symbols') and self.executor.symbols:
                                self.metrics.set_symbols_loaded(len(self.executor.symbols))
                            
                            logger.info(
                                "strategy_cycle_completed",
                                orders_executed=len(executed_orders),
                                duration=cycle_duration
                            )
                        except Exception as e:
                            # Record cycle error
                            self.metrics.record_cycle_error(type(e).__name__)
                            raise
                    else:
                        logger.debug("market_closed")
                    
                    last_cycle_time = current_time
                
                # Sleep briefly to avoid busy-waiting
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("keyboard_interrupt")
                break
            except Exception as e:
                logger.error("bot_error", error=str(e), exc_info=True)
                self.metrics.record_cycle_error("general_error")
                time.sleep(10)  # Wait before retrying
        
        logger.info("bot_stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='QuantShift Unified Trading Bot V3')
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to config file (e.g., config/equity_config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Initialize and run bot
    bot = QuantShiftUnifiedBot(args.config)
    bot.run()


if __name__ == '__main__':
    main()
