"""Stable broker order ids."""

from uuid import UUID

from quantshift_core.order_identity import (
    alpaca_client_order_id,
    coinbase_client_order_id,
    kraken_txid_for_userref,
    kraken_userref,
)


def test_order_ids_stay_the_same_for_the_same_decision():
    args = ("quantshift-equity", "AAPL", "buy", "2026-11-17T14:30:00Z", "entry")

    assert alpaca_client_order_id(*args) == alpaca_client_order_id(*args)
    assert coinbase_client_order_id(*args) == coinbase_client_order_id(*args)


def test_a_different_bar_is_a_different_order():
    first = alpaca_client_order_id("quantshift-equity", "AAPL", "buy", "2026-11-17T14:30:00Z", "entry")
    second = alpaca_client_order_id("quantshift-equity", "AAPL", "buy", "2026-11-18T14:30:00Z", "entry")

    assert first != second


def test_ids_match_broker_limits():
    alpaca_id = alpaca_client_order_id("quantshift-crypto", "BTC-USD", "sell", "2026-11-17T15:00:00Z", "stop-42000")
    coinbase_id = coinbase_client_order_id("quantshift-crypto", "BTC-USD", "sell", "2026-11-17T15:00:00Z", "stop-42000")

    assert len(alpaca_id) <= 48
    assert alpaca_id.isalnum()
    UUID(coinbase_id)


def test_kraken_userref_is_stable_and_positive():
    args = ("quantshift-kraken", "XBTUSD", "buy", "2026-11-17T15:00:00Z", "entry")
    userref = kraken_userref(*args)

    assert userref == kraken_userref(*args)
    assert 1 <= userref <= 2**31 - 1


def test_canceled_kraken_order_does_not_block_the_same_decision():
    userref = 42
    canceled = {"T1": {"userref": userref, "status": "canceled"}}
    filled = {"T2": {"userref": userref, "status": "closed"}}

    assert kraken_txid_for_userref(canceled, userref) is None
    assert kraken_txid_for_userref(filled, userref) == "T2"
