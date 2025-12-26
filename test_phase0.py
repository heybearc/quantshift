#!/usr/bin/env python3
"""
Phase 0 Testing Script - Verify broker-agnostic architecture works
"""
import os
import sys

# Set up environment
os.environ['APCA_API_KEY_ID'] = 'PKUNCOV2CO3Y7XBI47CWOPCTBX'
os.environ['APCA_API_SECRET_KEY'] = '739TxLJoKbvSyV1yvioZxVkWZxdJSnXCPFPaN6ZdQjjL'

sys.path.insert(0, 'packages/core/src')

print("=" * 60)
print("Phase 0 Testing - Broker-Agnostic Architecture")
print("=" * 60)

# Test 1: Import strategy framework
print("\n[Test 1] Importing strategy framework...")
try:
    from quantshift_core.strategies import BaseStrategy, MACrossoverStrategy, Signal, SignalType
    print("✓ Strategy framework imported successfully")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Initialize strategy
print("\n[Test 2] Initializing MA Crossover strategy...")
try:
    config = {
        'short_window': 20,
        'long_window': 50,
        'atr_period': 14,
        'risk_per_trade': 0.02,
        'max_positions': 5
    }
    strategy = MACrossoverStrategy(config=config)
    print(f"✓ Strategy initialized: {strategy.name}")
    print(f"  - Short window: {strategy.short_window}")
    print(f"  - Long window: {strategy.long_window}")
    print(f"  - Risk per trade: {strategy.risk_per_trade * 100}%")
except Exception as e:
    print(f"✗ Failed to initialize strategy: {e}")
    sys.exit(1)

# Test 3: Initialize Alpaca client
print("\n[Test 3] Connecting to Alpaca API...")
try:
    from alpaca.trading.client import TradingClient
    
    alpaca_client = TradingClient(
        api_key=os.getenv('APCA_API_KEY_ID'),
        secret_key=os.getenv('APCA_API_SECRET_KEY'),
        paper=True
    )
    
    account = alpaca_client.get_account()
    print(f"✓ Connected to Alpaca (Paper Trading)")
    print(f"  - Account equity: ${float(account.equity):,.2f}")
    print(f"  - Buying power: ${float(account.buying_power):,.2f}")
except Exception as e:
    print(f"✗ Failed to connect to Alpaca: {e}")
    sys.exit(1)

# Test 4: Initialize Alpaca executor
print("\n[Test 4] Initializing Alpaca executor...")
try:
    sys.path.insert(0, 'apps/bots/equity')
    from alpaca_executor import AlpacaExecutor
    
    symbols = ['SPY', 'QQQ']
    executor = AlpacaExecutor(
        strategy=strategy,
        alpaca_client=alpaca_client,
        symbols=symbols
    )
    print(f"✓ Executor initialized")
    print(f"  - Strategy: {executor.strategy.name}")
    print(f"  - Symbols: {executor.symbols}")
except Exception as e:
    print(f"✗ Failed to initialize executor: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Fetch market data for stocks
print("\n[Test 5] Fetching stock market data...")
try:
    import pandas as pd
    
    for symbol in ['SPY', 'QQQ']:
        market_data = executor.get_market_data(symbol, days=60)
        print(f"✓ Fetched {len(market_data)} bars for {symbol}")
        print(f"  - Latest close: ${market_data['close'].iloc[-1]:.2f}")
        print(f"  - Date range: {market_data.index[0]} to {market_data.index[-1]}")
except Exception as e:
    print(f"✗ Failed to fetch market data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Get account and positions
print("\n[Test 6] Getting account and positions...")
try:
    account = executor.get_account()
    positions = executor.get_positions()
    
    print(f"✓ Account data retrieved")
    print(f"  - Equity: ${account.equity:,.2f}")
    print(f"  - Cash: ${account.cash:,.2f}")
    print(f"  - Positions: {len(positions)}")
    
    if positions:
        for pos in positions:
            print(f"    • {pos.symbol}: {pos.quantity} shares @ ${pos.current_price:.2f}")
except Exception as e:
    print(f"✗ Failed to get account/positions: {e}")
    sys.exit(1)

# Test 7: Test signal generation (dry run)
print("\n[Test 7] Testing signal generation (dry run)...")
try:
    market_data = executor.get_market_data('SPY', days=90)
    account = executor.get_account()
    positions = executor.get_positions()
    
    signals = strategy.generate_signals(market_data, account, positions)
    
    print(f"✓ Signal generation successful")
    print(f"  - Signals generated: {len(signals)}")
    
    if signals:
        for signal in signals:
            print(f"    • {signal.signal_type.value.upper()} {signal.symbol} @ ${signal.price:.2f}")
            print(f"      Reason: {signal.reason}")
    else:
        print("    • No signals (HOLD)")
        
except Exception as e:
    print(f"✗ Failed to generate signals: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("Phase 0 Testing Complete - All Tests Passed! ✓")
print("=" * 60)
print("\nNext Steps:")
print("1. Deploy run_bot_v2.py to production container")
print("2. Update systemd service to use V2 bot")
print("3. Begin Phase 1: Backtesting")
print()
