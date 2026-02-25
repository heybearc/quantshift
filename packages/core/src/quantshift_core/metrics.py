"""
Prometheus metrics for QuantShift trading bots.

This module provides a reusable metrics class that can be used by:
- Current monolithic bots
- Future modular components (coordinator, workers, services)

Metrics are exported via HTTP endpoint for Prometheus scraping.
"""

from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server
import structlog
import time
from typing import Optional

logger = structlog.get_logger()


class BotMetrics:
    """
    Prometheus metrics for a trading bot component.
    
    Usage:
        metrics = BotMetrics(component_name="quantshift_equity", port=9100)
        metrics.record_heartbeat()
        metrics.record_cycle_duration(5.2)
        metrics.record_signal_generated("bollinger")
    """
    
    def __init__(self, component_name: str, port: int = 9100):
        """
        Initialize metrics for a bot component.
        
        Args:
            component_name: Name of the component (e.g., "quantshift_equity", "coordinator")
            port: HTTP port for metrics endpoint (default: 9100)
        """
        self.component_name = component_name
        self.port = port
        
        # Component info
        self.info = Info(
            f'{component_name}_info',
            'Component information'
        )
        
        # Health metrics
        self.heartbeat = Gauge(
            f'{component_name}_heartbeat_seconds',
            'Last heartbeat timestamp (Unix time)',
            ['component']
        )
        
        self.cycle_duration = Histogram(
            f'{component_name}_cycle_duration_seconds',
            'Time taken to complete a cycle',
            ['component'],
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
        )
        
        self.cycle_errors = Counter(
            f'{component_name}_cycle_errors_total',
            'Total number of cycle errors',
            ['component', 'error_type']
        )
        
        self.symbols_loaded = Gauge(
            f'{component_name}_symbols_loaded',
            'Number of symbols currently loaded',
            ['component']
        )
        
        # Business metrics
        self.portfolio_value = Gauge(
            f'{component_name}_portfolio_value_usd',
            'Current portfolio value in USD',
            ['component', 'bot']
        )
        
        self.daily_pnl = Gauge(
            f'{component_name}_daily_pnl_usd',
            'Daily profit/loss in USD',
            ['component', 'bot']
        )
        
        self.positions_open = Gauge(
            f'{component_name}_positions_open',
            'Number of open positions',
            ['component', 'bot']
        )
        
        self.signals_generated = Counter(
            f'{component_name}_signals_generated_total',
            'Total number of signals generated',
            ['component', 'bot', 'strategy']
        )
        
        self.orders_executed = Counter(
            f'{component_name}_orders_executed_total',
            'Total number of orders executed',
            ['component', 'bot', 'side']
        )
        
        # Performance metrics
        self.api_latency = Histogram(
            f'{component_name}_api_latency_seconds',
            'API call latency',
            ['component', 'api', 'endpoint'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.market_data_age = Gauge(
            f'{component_name}_market_data_age_seconds',
            'Age of market data in seconds',
            ['component', 'symbol']
        )
        
        # Watchdog metrics
        self.watchdog_notifications = Counter(
            f'{component_name}_watchdog_notifications_total',
            'Total number of watchdog notifications sent',
            ['component']
        )
        
        self.watchdog_restarts = Counter(
            f'{component_name}_watchdog_restarts_total',
            'Total number of watchdog-triggered restarts',
            ['component']
        )
        
        logger.info(
            "metrics_initialized",
            component=component_name,
            port=port
        )
    
    def start_server(self):
        """Start HTTP server for metrics endpoint."""
        try:
            start_http_server(self.port)
            logger.info(
                "metrics_server_started",
                component=self.component_name,
                port=self.port,
                endpoint=f"http://localhost:{self.port}/metrics"
            )
        except OSError as e:
            if "Address already in use" in str(e):
                logger.warning(
                    "metrics_server_already_running",
                    component=self.component_name,
                    port=self.port
                )
            else:
                raise
    
    def set_info(self, version: str, environment: str):
        """Set component information."""
        self.info.info({
            'version': version,
            'environment': environment,
            'component': self.component_name
        })
    
    def record_heartbeat(self):
        """Record heartbeat timestamp."""
        self.heartbeat.labels(component=self.component_name).set(time.time())
    
    def record_cycle_duration(self, duration: float):
        """Record cycle duration in seconds."""
        self.cycle_duration.labels(component=self.component_name).observe(duration)
    
    def record_cycle_error(self, error_type: str):
        """Record a cycle error."""
        self.cycle_errors.labels(
            component=self.component_name,
            error_type=error_type
        ).inc()
    
    def set_symbols_loaded(self, count: int):
        """Set number of symbols loaded."""
        self.symbols_loaded.labels(component=self.component_name).set(count)
    
    def set_portfolio_value(self, value: float, bot_name: str):
        """Set portfolio value in USD."""
        self.portfolio_value.labels(
            component=self.component_name,
            bot=bot_name
        ).set(value)
    
    def set_daily_pnl(self, pnl: float, bot_name: str):
        """Set daily P&L in USD."""
        self.daily_pnl.labels(
            component=self.component_name,
            bot=bot_name
        ).set(pnl)
    
    def set_positions_open(self, count: int, bot_name: str):
        """Set number of open positions."""
        self.positions_open.labels(
            component=self.component_name,
            bot=bot_name
        ).set(count)
    
    def record_signal_generated(self, bot_name: str, strategy: str):
        """Record a signal generation."""
        self.signals_generated.labels(
            component=self.component_name,
            bot=bot_name,
            strategy=strategy
        ).inc()
    
    def record_order_executed(self, bot_name: str, side: str):
        """Record an order execution."""
        self.orders_executed.labels(
            component=self.component_name,
            bot=bot_name,
            side=side
        ).inc()
    
    def record_api_call(self, api: str, endpoint: str, duration: float):
        """Record API call latency."""
        self.api_latency.labels(
            component=self.component_name,
            api=api,
            endpoint=endpoint
        ).observe(duration)
    
    def set_market_data_age(self, symbol: str, age: float):
        """Set age of market data in seconds."""
        self.market_data_age.labels(
            component=self.component_name,
            symbol=symbol
        ).set(age)
    
    def record_watchdog_notification(self):
        """Record a watchdog notification."""
        self.watchdog_notifications.labels(component=self.component_name).inc()
    
    def record_watchdog_restart(self):
        """Record a watchdog restart."""
        self.watchdog_restarts.labels(component=self.component_name).inc()


class MetricsContext:
    """
    Context manager for timing operations.
    
    Usage:
        with MetricsContext(metrics.api_latency, labels={'api': 'alpaca', 'endpoint': 'get_bars'}):
            data = alpaca.get_bars(...)
    """
    
    def __init__(self, histogram: Histogram, labels: Optional[dict] = None):
        self.histogram = histogram
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.histogram.labels(**self.labels).observe(duration)
        return False
