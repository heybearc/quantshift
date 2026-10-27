#!/usr/bin/env python3
"""
QuantShift Automated Failover Monitor

Runs on STANDBY bot container (CT 101).
Monitors PRIMARY bot heartbeat from PostgreSQL database.
Triggers failover if primary is down for > 60 seconds.

Failover procedure:
1. Promote standby Redis to master
2. Update bot status in database to PRIMARY
3. Start standby bot processes
4. Send alert notification

Failover runs only when every bot heartbeat is stale. One dead bot
stays on the primary host, where systemd restarts that process.

Usage:
    python failover_monitor.py

Systemd service:
    /etc/systemd/system/quantshift-failover-monitor.service
"""

import os
import sys
import time
import subprocess
import psycopg2
from datetime import datetime, timezone
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
        """Promote standby Redis to master."""
        try:
            logger.info("promoting_redis_to_master")
            
            # Promote to master
            result = subprocess.run(
                ['redis-cli', '-a', self.redis_password, 'SLAVEOF', 'NO', 'ONE'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error("redis_promotion_failed", stderr=result.stderr)
                return False
            
            logger.info("redis_promoted_to_master", stdout=result.stdout.strip())
            
            # Verify promotion
            result = subprocess.run(
                ['redis-cli', '-a', self.redis_password, 'INFO', 'replication'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'role:master' in result.stdout:
                logger.info("redis_promotion_verified")
                return True
            else:
                logger.error("redis_promotion_verification_failed", output=result.stdout)
                return False
                
        except Exception as e:
            logger.error("redis_promotion_error", error=str(e), exc_info=True)
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
        """Start bot systemd service."""
        try:
            logger.info("starting_bot_service", service=service_name)
            
            result = subprocess.run(
                ['systemctl', 'start', service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error("service_start_failed", service=service_name, stderr=result.stderr)
                return False
            
            # Verify service started
            time.sleep(5)
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.stdout.strip() == 'active':
                logger.info("service_started_successfully", service=service_name)
                return True
            else:
                logger.error("service_not_active", service=service_name, status=result.stdout.strip())
                return False
                
        except Exception as e:
            logger.error("service_start_error", service=service_name, error=str(e), exc_info=True)
            return False
    
    def send_alert(self, message: str):
        """Send alert notification (placeholder for future implementation)."""
        logger.critical("FAILOVER_ALERT", message=message)
        # TODO: Integrate with Alertmanager or email notification
        # For now, just log critically
    
    def perform_failover(self):
        """
        Perform complete failover procedure.
        
        Steps:
        1. Promote Redis to master
        2. Update database status
        3. Start bot services
        4. Send alert
        """
        if self.failover_in_progress:
            logger.warning("failover_already_in_progress")
            return False
        
        # Check cooldown
        if self.last_failover_time:
            time_since_last = time.time() - self.last_failover_time
            if time_since_last < self.failover_cooldown:
                logger.warning(
                    "failover_cooldown_active",
                    seconds_remaining=self.failover_cooldown - time_since_last
                )
                return False
        
        self.failover_in_progress = True
        failover_start_time = time.time()
        
        try:
            logger.critical("FAILOVER_INITIATED", timestamp=datetime.now(timezone.utc).isoformat())
            
            # Step 1: Promote Redis
            if not self.promote_redis_to_master():
                raise Exception("Redis promotion failed")
            
            # Step 2: Update database status and start every book.
            for bot_name in BOTS:
                if not self.update_bot_status_to_primary(bot_name):
                    raise Exception(f"Failed to update {bot_name} status")
                if not self.start_bot_service(bot_name):
                    raise Exception(f"Failed to start {bot_name}")
            
            # Step 3: Send alert
            failover_duration = time.time() - failover_start_time
            self.send_alert(
                f"Failover completed successfully in {failover_duration:.1f} seconds. "
                f"Standby is now PRIMARY."
            )
            
            logger.critical(
                "FAILOVER_COMPLETED",
                duration_seconds=failover_duration,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            self.last_failover_time = time.time()
            return True
            
        except Exception as e:
            logger.critical("FAILOVER_FAILED", error=str(e), exc_info=True)
            self.send_alert(f"Failover FAILED: {str(e)}")
            return False
            
        finally:
            self.failover_in_progress = False
    
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
                
                # One stale book is a process restart on the primary host.
                # Promote only when the whole primary has stopped heartbeating.
                if len(unhealthy) == len(BOTS):
                    logger.warning("primary_unhealthy_detected", bots=unhealthy)
                    self.perform_failover()
                elif unhealthy:
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
