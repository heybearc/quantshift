"""Equity executor must not open a short, and must remember the broker stop."""

import sys
import types
from datetime import datetime, timezone
from types import SimpleNamespace


def _stub_modules():
    if "alpaca.trading.client" in sys.modules:
        return

    def pkg(name):
        module = types.ModuleType(name)
        sys.modules[name] = module
        return module

    pkg("alpaca")
    pkg("alpaca.trading")
    client = pkg("alpaca.trading.client")
    requests = pkg("alpaca.trading.requests")
    enums = pkg("alpaca.trading.enums")
    pkg("alpaca.data")
    historical = pkg("alpaca.data.historical")
    data_requests = pkg("alpaca.data.requests")
    timeframe = pkg("alpaca.data.timeframe")
    coinbase = pkg("coinbase")
    rest = pkg("coinbase.rest")

    class Req:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class OrderSide:
        BUY = SimpleNamespace(value="buy")
        SELL = SimpleNamespace(value="sell")

    class RESTClient:
        pass

    client.TradingClient = object
    requests.GetOrdersRequest = Req
    requests.MarketOrderRequest = Req
    requests.LimitOrderRequest = Req
    requests.StopOrderRequest = Req
    requests.GetOrderByIdRequest = Req
    requests.ClosePositionRequest = Req
    enums.OrderSide = OrderSide
    enums.TimeInForce = SimpleNamespace(DAY="day", GTC="gtc")
    enums.QueryOrderStatus = SimpleNamespace(OPEN="open", ALL="all", CLOSED="closed")
    enums.OrderStatus = SimpleNamespace(FILLED="filled", PARTIALLY_FILLED="partial")
    enums.OrderClass = SimpleNamespace(BRACKET="bracket")
    historical.StockHistoricalDataClient = object
    data_requests.StockBarsRequest = Req
    timeframe.TimeFrame = SimpleNamespace(Day="day")
    rest.RESTClient = RESTClient
    coinbase.rest = rest

    class _Mods(types.ModuleType):
        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError(name)
            dummy = type(name, (), {})
            setattr(self, name, dummy)
            return dummy

    pandas = _Mods("pandas")
    numpy = _Mods("numpy")
    sys.modules["pandas"] = pandas
    sys.modules["numpy"] = numpy
    structlog = pkg("structlog")

    class _Log:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    structlog.get_logger = lambda *args, **kwargs: _Log()


_stub_modules()

from quantshift_core.executors.alpaca_executor import AlpacaExecutor
from quantshift_core.strategies.base_strategy import Account, Signal, SignalType


class Broker:
    def __init__(self, positions, orders=None, close=True):
        self.positions = positions
        self.orders = orders or []
        self.closed = []
        self.submitted = []
        self.cancelled = []
        self._close = close
        if close:
            self.close_position = self._close_position

    def get_all_positions(self):
        return list(self.positions)

    def get_orders(self, filter=None):
        return list(self.orders)

    def cancel_order_by_id(self, order_id):
        self.cancelled.append(order_id)

    def _close_position(self, symbol, close_options=None):
        self.closed.append((symbol, getattr(close_options, "qty", None)))
        self.positions = [pos for pos in self.positions if pos.symbol != symbol]
        side = "buy" if any(getattr(pos, "side", None) == "short" for pos in []) else "sell"
        return SimpleNamespace(
            id="close-1",
            symbol=symbol,
            qty=close_options.qty,
            side=SimpleNamespace(value=side),
            type=SimpleNamespace(value="market"),
            status=SimpleNamespace(value="accepted"),
            submitted_at=None,
        )

    def submit_order(self, request):
        self.submitted.append(request)
        return SimpleNamespace(
            id="market-1",
            symbol=request.symbol,
            qty=request.qty,
            side=request.side,
            type=SimpleNamespace(value="market"),
            status=SimpleNamespace(value="accepted"),
            submitted_at=None,
        )


def _position(symbol, qty, side, price=100):
    return SimpleNamespace(
        symbol=symbol,
        qty=str(qty),
        side=side,
        avg_entry_price=str(price),
        current_price=str(price),
        market_value=str(qty * price),
        unrealized_pl="0",
        unrealized_plpc="0",
    )


def _signal(kind, symbol, size):
    return Signal(
        signal_type=kind,
        symbol=symbol,
        timestamp=datetime.now(timezone.utc),
        price=100.0,
        position_size=size,
        reason="test exit",
    )


def _executor(broker):
    return AlpacaExecutor(SimpleNamespace(name="Test"), broker, symbols=["AAPL"])


def test_short_with_positive_qty_keeps_the_buy_stop():
    broker = Broker(
        [_position("AAPL", 5, "short")],
        orders=[
            SimpleNamespace(id="sell-stop", symbol="AAPL", side="sell", stop_price=90, legs=None),
            SimpleNamespace(id="buy-stop", symbol="AAPL", side="buy", stop_price=110, legs=None),
        ],
    )
    positions = _executor(broker).get_positions()

    assert positions[0].side == "short"
    assert positions[0].quantity == -5
    assert positions[0].metadata["stop_loss"] == 110


def test_held_bracket_stop_is_stored_and_a_canceled_stop_is_not():
    limit = SimpleNamespace(symbol="BA", side="sell", status="new", stop_price=None, legs=None)
    parent = SimpleNamespace(
        symbol="BA",
        side="buy",
        status="filled",
        stop_price=None,
        legs=[
            SimpleNamespace(symbol="BA", side="sell", status="new", stop_price=None, legs=None),
            SimpleNamespace(symbol="BA", side="sell", status="canceled", stop_price=190, legs=None),
            SimpleNamespace(symbol="BA", side="sell", status="held", stop_price=177.51, legs=None),
        ],
    )
    broker = Broker([_position("BA", 21, "long")], orders=[])

    def get_orders(filter=None):
        status = getattr(filter, "status", None)
        status = str(getattr(status, "value", status) or "").lower()
        if status == "all":
            return [parent]
        return [limit]

    broker.get_orders = get_orders
    positions = _executor(broker).get_positions()

    assert positions[0].metadata["stop_loss"] == 177.51


def test_sell_larger_than_the_long_closes_only_the_long_and_cancels_the_bracket():
    broker = Broker(
        [_position("AAPL", 5, "long")],
        orders=[SimpleNamespace(id="bracket-stop", symbol="AAPL", side="sell", stop_price=95, legs=None)],
    )
    order = _executor(broker).execute_signal(_signal(SignalType.SELL, "AAPL", 12))

    assert order is not None
    assert broker.cancelled == ["bracket-stop"]
    assert broker.closed == [("AAPL", "5")]
    assert broker.submitted == []


def test_sell_while_flat_submits_nothing():
    broker = Broker([])
    order = _executor(broker).execute_signal(_signal(SignalType.SELL, "AAPL", 5))

    assert order is None
    assert broker.closed == []
    assert broker.submitted == []


def test_failed_reduce_only_close_does_not_send_a_market_sell():
    broker = Broker([_position("AAPL", 5, "long")])

    def explode(symbol, close_options=None):
        raise RuntimeError("position already flat")

    broker.close_position = explode
    order = _executor(broker).execute_signal(_signal(SignalType.SELL, "AAPL", 5))

    assert order is None
    assert broker.submitted == []


def test_without_broker_close_a_short_is_bought_back():
    broker = Broker([_position("AAPL", 4, "short")], close=False)
    order = _executor(broker).execute_signal(_signal(SignalType.SELL, "AAPL", 4))

    assert order is not None
    assert len(broker.submitted) == 1
    assert broker.submitted[0].side.value == "buy"
    assert broker.submitted[0].qty == 4.0


def test_cycle_covers_a_short_before_strategies_run():
    broker = Broker([_position("AAPL", 3, "short", price=50)])
    executor = _executor(broker)
    executor.is_market_open = lambda: True
    executor.get_account = lambda: Account(100000, 100000, 100000, 100000)
    class Bars:
        def __len__(self):
            return 250

    executor.get_market_data = lambda symbol, days=90, timeframe=None: Bars()
    seen = {}

    def generate_signals(market_data, account, positions):
        seen["sides"] = [pos.side for pos in positions]
        return []

    executor.strategy.generate_signals = generate_signals
    result = executor.run_strategy_cycle()

    assert broker.closed == [("AAPL", "3")]
    assert seen["sides"] == []
    assert len(result["orders_executed"]) == 1
