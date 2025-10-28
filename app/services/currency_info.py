# app/services/currency_info.py
import json
import urllib.request
from typing import List, Tuple
from functools import lru_cache

API_URL_CODES = (
    "https://open.er-api.com/v6/latest/USD"
)

PREDEFINED_CURRENCIES = [
    ("USD", "United States Dollar", "$"),
    ("EUR", "Euro", "€"),
    ("GBP", "British Pound Sterling", "£"),
    ("JPY", "Japanese Yen", "¥"),
    ("CHF", "Swiss Franc", "Fr"),
    ("CAD", "Canadian Dollar", "C$"),
    ("UAH", "Ukrainian Hryvnia", "₴"),
    ("AUD", "Australian Dollar", "A$"),
    ("CNY", "Chinese Yuan", "¥"),
    ("INR", "Indian Rupee", "₹"),
]


@lru_cache(maxsize=1)
def fetch_currency_list() -> List[Tuple[str, str]]:
    """
    Fetches a list of available currency codes and names.
    Returns a list of tuples: [('USD', 'United States Dollar'), ('EUR', 'Euro'), ...].
    Uses a fallback predefined list if the API fails.
    """
    try:
        with urllib.request.urlopen(API_URL_CODES, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("result") == "success" and "rates" in data:
                    codes = list(data["rates"].keys())
                    return [(code, code) for code in sorted(codes)]
            else:
                print(f"[Currency API Error] Status: {response.status}")

    except Exception as e:
        print(f"[Currency API Client Error] {e}")

    print("[Currency API] Using predefined currency list as fallback.")
    return [(code, name) for code, name, symbol in PREDEFINED_CURRENCIES]


_COMMON_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CHF": "Fr",
    "CAD": "C$",
    "UAH": "₴",
    "AUD": "A$",
    "CNY": "¥",
    "INR": "₹",
}


def get_default_symbol(currency_code: str) -> str:
    """Gets a common default symbol for a currency code."""
    return _COMMON_SYMBOLS.get(
        currency_code, currency_code
    )
