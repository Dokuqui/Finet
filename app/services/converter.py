from app.db import settings as db_settings
from functools import lru_cache
from typing import Dict

ALL_CURRENCIES = sorted(["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "UAH"])


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
    """
    Returns a symbol for a given currency code.
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CHF": "Fr",
        "CAD": "C$",
        "UAH": "₴",
    }
    return symbols.get(currency_code, currency_code)


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
