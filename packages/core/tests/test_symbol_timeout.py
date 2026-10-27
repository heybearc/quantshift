"""A hung Coinbase product list must return the fixed symbols."""

from quantshift_core.symbol_universe import SymbolUniverse


def test_coinbase_product_timeout_uses_the_curated_list():
    universe = SymbolUniverse("coinbase")

    def hang(url, timeout):
        raise TimeoutError(url)

    universe._read_json_deadline = hang
    symbols = universe._fetch_coinbase_symbols()
    assert symbols[0] == "BTC-USD"
    assert len(symbols) >= 40
