from app.db import settings as db_settings
from functools import lru_cache
from typing import Dict, List


@lru_cache(maxsize=1)
def get_active_currencies_data() -> List[dict]:
    """Fetches and caches the list of active currencies from DB"""
    return db_settings.get_active_currencies()


@lru_cache(maxsize=1)
def get_active_currency_codes() -> List[str]:
    """Returns just the codes of active currencies"""
    return sorted([c["code"] for c in get_active_currencies_data()])


@lru_cache(maxsize=1)
def get_currency_symbol_map() -> Dict[str, str]:
    """Fetches and caches the symbol map from DB"""
    symbols = {
        c["code"]: c.get("symbol") or c["code"] for c in get_active_currencies_data()
    }
    return symbols


@lru_cache(maxsize=1)
def get_base_currency() -> str:
    """
    Returns the stored base currency (e.g., "EUR").
    """
    return db_settings.get_base_currency()


@lru_cache(maxsize=1)
def get_conversion_rates() -> dict[str, float]:
    """
    Returns a dictionary of all exchange rates relative to the base currency.
    e.g., {'USD': 1.08, 'EUR': 1.0, 'GBP': 0.86, ...}
    """
    return db_settings.get_exchange_rates()


def get_currency_symbol(currency_code: str) -> str:
    """Returns the stored symbol for a currency code, or the code itself."""
    symbol_map = get_currency_symbol_map()
    return symbol_map.get(currency_code, currency_code)


def convert_to_base(
    amount: float, currency: str, rates: Dict[str, float] = None
) -> float:
    """
    Converts a given amount from its currency to the base currency.

    Rates are stored as "1 Base = X Foreign" (e.g., 1 EUR = 1.08 USD).
    To convert USD to EUR, we must DIVIDE.
    e.g., 108 USD / 1.08 = 100 EUR.

    :param rates: Optionally pass in rates to avoid re-fetching.
    """
    if amount == 0:
        return 0.0

    if rates is None:
        rates = get_conversion_rates()

    base_currency = get_base_currency()

    if currency == base_currency:
        return amount

    rate = rates.get(currency)
    if rate is None or rate == 0:
        print(f"[Warning] No conversion rate for {currency}. Returning 0.")
        return 0.0

    return amount / rate


def clear_caches():
    get_active_currencies_data.cache_clear()
    get_active_currency_codes.cache_clear()
    get_currency_symbol_map.cache_clear()
    get_base_currency.cache_clear()
    get_conversion_rates.cache_clear()
    print("[Cache] Cleared converter caches.")
