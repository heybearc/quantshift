"""A hung Coinbase product list must return the fixed symbols."""

from quantshift_core.symbol_universe import SymbolUniverse


def test_unknown_exchange_does_not_drop_the_rest_of_the_asset_list():
    universe = SymbolUniverse("alpaca", api_client=object())
    rows = [
        {"symbol": "TXSESTOCK", "tradable": True, "fractionable": True, "shortable": True, "exchange": "TXSE"},
        {"symbol": "AAPL", "tradable": True, "fractionable": True, "shortable": True, "exchange": "NASDAQ"},
        {"symbol": "DEAD", "tradable": False, "fractionable": True, "shortable": True, "exchange": "NYSE"},
        {"symbol": "SPY", "tradable": True, "fractionable": True, "shortable": True, "exchange": "ARCA"},
    ]

    class Client:
        def get(self, path, params):
            assert path == "/assets"
            assert params["status"] == "active"
            assert params["asset_class"] == "us_equity"
            return rows

    universe.api_client = Client()
    symbols = universe._fetch_alpaca_symbols()
    assert "AAPL" in symbols
    assert "SPY" in symbols
    assert "TXSESTOCK" not in symbols
    assert "DEAD" not in symbols


def test_coinbase_product_timeout_uses_the_curated_list():
    universe = SymbolUniverse("coinbase")

    def hang(url, timeout):
        raise TimeoutError(url)

    universe._read_json_deadline = hang
    symbols = universe._fetch_coinbase_symbols()
    assert symbols[0] == "BTC-USD"
    assert len(symbols) >= 40
