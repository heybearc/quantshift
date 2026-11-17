#!/usr/bin/env python3
"""
QuantShift bot heartbeat monitor.

Runs on the spare bot container (CT 101). It watches primary heartbeats and
logs when they go stale. It does not promote Redis and it does not start bots.

One process per bot runs on CT100. systemd restarts that process. CT101 stays
a spare until an operator starts it after CT100 is confirmed stopped.

Usage:
    python failover_monitor.py

Systemd service:
    /etc/systemd/system/quantshift-failover-monitor.service
"""

import os
import time
import psycopg2
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

BOTS = (
    "quantshift-equity",
    "quantshift-crypto",
    "quantshift-kraken",
)


class FailoverMonitor:
    """
    Monitors primary bot health and triggers failover if needed.
    """
    
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        
        self.check_interval = 10  # Check every 10 seconds
        self.heartbeat_timeout = 60  # Failover if no heartbeat for 60 seconds
        
        self.db_conn = None
        self.failover_in_progress = False
        self.last_failover_time = None
        self.failover_cooldown = 300  # 5 minutes between failovers
        self._refusal_logged = False
        
        logger.info(
            "failover_monitor_initialized",
            check_interval=self.check_interval,
            heartbeat_timeout=self.heartbeat_timeout
        )
    
    def connect_db(self):
        """Connect to PostgreSQL database."""
        try:
            if self.db_conn:
                self.db_conn.close()
            
            self.db_conn = psycopg2.connect(self.db_url)
            logger.info("database_connected")
            return True
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            return False
    
    def check_primary_heartbeat(self, bot_name: str) -> dict:
        """
        Check primary bot heartbeat from database.
        
        Returns:
            dict with keys: healthy, seconds_since_heartbeat, status
        """
        try:
            if not self.db_conn:
                if not self.connect_db():
                    return {'healthy': False, 'seconds_since_heartbeat': 999, 'status': 'db_error'}
            
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT 
                    status,
                    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) as seconds_since_heartbeat,
                    last_heartbeat
                FROM bot_status
                WHERE bot_name = %s
            """, (bot_name,))
            
            row = cursor.fetchone()
            
            if not row:
                logger.warning("bot_not_found_in_database", bot_name=bot_name)
                return {'healthy': False, 'seconds_since_heartbeat': 999, 'status': 'not_found'}
            
            status, seconds_since_heartbeat, last_heartbeat = row
            
            # Convert to float and handle None
            seconds_ago = float(seconds_since_heartbeat) if seconds_since_heartbeat is not None else 999.0
            
            # If negative, heartbeat is in the future (clock skew) - treat as healthy
            if seconds_ago < 0:
                seconds_ago = 0
            
            healthy = (
                status == 'PRIMARY' and 
                seconds_ago < self.heartbeat_timeout
            )
            
            return {
                'healthy': healthy,
                'seconds_since_heartbeat': seconds_ago,
                'status': status,
                'last_heartbeat': last_heartbeat
            }
            
        except Exception as e:
            logger.error("heartbeat_check_failed", error=str(e), exc_info=True)
            # Reconnect on next attempt
            if self.db_conn:
                try:
                    self.db_conn.close()
                except:
                    pass
                self.db_conn = None
            return {'healthy': False, 'seconds_since_heartbeat': 999, 'status': 'error'}
    
    def promote_redis_to_master(self):
        """Redis promotion is disabled. Two masters can both trade."""
        logger.critical("redis_promotion_blocked")
        return False
    
    def update_bot_status_to_primary(self, bot_name: str):
        """Update bot status in database to PRIMARY."""
        try:
            if not self.db_conn:
                if not self.connect_db():
                    return False
            
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE bot_status
                SET status = 'PRIMARY',
                    updated_at = NOW()
                WHERE bot_name = %s
            """, (bot_name,))
            
            self.db_conn.commit()
            logger.info("bot_status_updated_to_primary", bot_name=bot_name)
            return True
            
        except Exception as e:
            logger.error("bot_status_update_failed", error=str(e), exc_info=True)
            return False
    
    def start_bot_service(self, service_name: str):
        """Standby bot starts are disabled. The spare must not trade over the primary."""
        logger.critical("standby_bot_start_blocked", service=service_name)
        return False
    
    def send_alert(self, message: str):
        """Send alert notification (placeholder for future implementation)."""
        logger.critical("FAILOVER_ALERT", message=message)
        # TODO: Integrate with Alertmanager or email notification
        # For now, just log critically
    
    def perform_failover(self):
        """Log a stale primary and leave Redis and the bots where they are."""
        logger.critical(
            "FAILOVER_REFUSED",
            message=(
                "Automatic promotion is disabled. Restart the affected bot on CT100. "
                "Start CT101 only after CT100 is confirmed stopped."
            ),
        )
        self.send_alert(
            "Primary heartbeats are stale. Redis was not promoted and no spare bots were started."
        )
        return False
    
    def run(self):
        """Main monitoring loop."""
        logger.info("failover_monitor_started")
        
        while True:
            try:
                health = {
                    bot_name: self.check_primary_heartbeat(bot_name)
                    for bot_name in BOTS
                }
                unhealthy = [
                    bot_name for bot_name, item in health.items() if not item['healthy']
                ]
                
                logger.debug(
                    "heartbeat_check",
                    **{
                        bot_name: item['seconds_since_heartbeat']
                        for bot_name, item in health.items()
                    }
                )
                
                # A stale book is restarted on CT100 by systemd. This process
                # only reports it. Promotion would make a second Redis master.
                if len(unhealthy) == len(BOTS):
                    logger.warning("primary_unhealthy_detected", bots=unhealthy)
                    if not self._refusal_logged:
                        self.perform_failover()
                        self._refusal_logged = True
                else:
                    self._refusal_logged = False
                    if unhealthy:
                        logger.warning("primary_bot_unhealthy", bots=unhealthy)
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("failover_monitor_stopped_by_user")
                break
            except Exception as e:
                logger.error("monitor_loop_error", error=str(e), exc_info=True)
                time.sleep(self.check_interval)
        
        logger.info("failover_monitor_stopped")


def main():
    """Main entry point."""
    monitor = FailoverMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
