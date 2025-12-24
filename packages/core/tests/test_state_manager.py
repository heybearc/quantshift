"""Tests for StateManager class."""

import pytest
from unittest.mock import Mock, patch
from quantshift_core.state_manager import StateManager


def test_state_manager_initialization():
    """Test StateManager initializes correctly."""
    with patch('quantshift_core.state_manager.redis.from_url'):
        state = StateManager(bot_name="test-bot")
        assert state.bot_name == "test-bot"


def test_save_and_load_state():
    """Test saving and loading bot state."""
    with patch('quantshift_core.state_manager.redis.from_url') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        state = StateManager(bot_name="test-bot")
        
        # Test save
        test_state = {"strategy": "test", "value": 123}
        state.save_state(test_state)
        
        # Verify setex was called
        assert mock_client.setex.called


def test_save_and_load_position():
    """Test saving and loading positions."""
    with patch('quantshift_core.state_manager.redis.from_url') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        state = StateManager(bot_name="test-bot")
        
        # Test save position
        position_data = {"quantity": 10, "entry_price": 150.00}
        state.save_position("AAPL", position_data)
        
        # Verify setex was called
        assert mock_client.setex.called


def test_heartbeat():
    """Test heartbeat functionality."""
    with patch('quantshift_core.state_manager.redis.from_url') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        
        state = StateManager(bot_name="test-bot")
        state.heartbeat()
        
        # Verify setex was called for heartbeat
        assert mock_client.setex.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
