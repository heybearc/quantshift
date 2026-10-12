"""Public Kraken market-data calls.

The installed Kraken client sends GET parameters in the request body.
Kraken only reads the query string, so those calls return
"EGeneral:Invalid arguments" and the bot skips the cycle.
"""

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


def kraken_public(method: str, params: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    """Call a public Kraken endpoint with the parameters on the query string."""
    query = urllib.parse.urlencode(params)
    url = f"https://api.kraken.com/0/public/{method}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "quantshift"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode())
    if not isinstance(payload, dict):
        return {"error": ["Unexpected Kraken response"]}
    return payload


def kraken_result_value(result: Optional[Dict[str, Any]]) -> Any:
    """Return the first result entry. Kraken renames pairs (XBTUSD arrives as XXBTZUSD)."""
    if not isinstance(result, dict):
        return None
    for key, value in result.items():
        if key != "last":
            return value
    return None
