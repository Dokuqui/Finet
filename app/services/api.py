import json
import urllib.request
from typing import Dict, Optional

API_URL_TEMPLATE = "https://open.er-api.com/v6/latest/{base}"


def fetch_latest_rates(base_currency: str) -> Optional[Dict[str, float]]:
    """
    Fetches the latest exchange rates for a given base currency.
    Returns a dict of rates or None on failure.
    """
    url = API_URL_TEMPLATE.format(base=base_currency)
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                print(f"[API Error] Status: {response.status}")
                return None

            data = json.loads(response.read().decode("utf-8"))

            if data.get("result") == "success":
                return data.get("rates")
            else:
                print(f"[API Error] Response: {data.get('error-type')}")
                return None

    except Exception as e:
        print(f"[API Client Error] {e}")
        return None
