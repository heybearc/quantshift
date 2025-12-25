#!/usr/bin/env python3
"""
QuantShift Equity Bot Runner with StateManager Integration
This script runs the existing Alpaca trading bot and integrates it with Redis state management
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime

# Add the core package to the path
sys.path.insert(0, '/opt/quantshift/packages/core/src')

from quantshift_core.state_manager import StateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuantShiftEquityBot:
    def __init__(self):
        self.bot_name = "equity-bot"
        self.state_manager = StateManager(
            bot_name=self.bot_name,
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', 6379)),
            redis_password=os.getenv('REDIS_PASSWORD', 'Cloudy_92!')
        )
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def update_state(self):
        """Update bot state in Redis"""
        state = {
            'status': 'running',
            'mode': 'paper',
            'last_update': datetime.utcnow().isoformat(),
            'strategy': 'multi-strategy',
            'account_balance': 10000.00,  # TODO: Get from actual Alpaca account
            'positions_count': 0,  # TODO: Get from actual positions
        }
        self.state_manager.save_state(state)
        
    def send_heartbeat(self):
        """Send heartbeat to Redis"""
        self.state_manager.heartbeat()
        
    def run(self):
        """Main bot loop"""
        logger.info(f"Starting {self.bot_name}...")
        
        # Initial state update
        self.update_state()
        
        # Main loop
        heartbeat_interval = 30  # seconds
        state_update_interval = 60  # seconds
        last_heartbeat = time.time()
        last_state_update = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Send heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat = current_time
                    logger.debug("Heartbeat sent")
                
                # Update state
                if current_time - last_state_update >= state_update_interval:
                    self.update_state()
                    last_state_update = current_time
                    logger.info("State updated")
                
                # Sleep to avoid busy waiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5)
        
        logger.info("Bot stopped")

if __name__ == '__main__':
    bot = QuantShiftEquityBot()
    bot.run()
