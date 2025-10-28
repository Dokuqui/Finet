from .connection import get_db_connection

DEFAULT_SETTINGS = {
    "base_currency": "EUR",
    "exchange_rates": {
        "USD": 1.08,
        "GBP": 0.86,
        "JPY": 162.5,
        "CHF": 0.97,
        "CAD": 1.48,
        "EUR": 1.0,
        "UAH": 43.0,
    },
}


def get_base_currency() -> str:
    """
    Get the application's base currency (e.g., 'EUR').
    """
    conn = get_db_connection()
    cur = conn.execute("SELECT value FROM app_settings WHERE key='base_currency'")
    row = cur.fetchone()
    conn.close()
    if row:
        return row["value"]
    else:
        print("[Warning] Base currency setting not found, using default.")
        return DEFAULT_SETTINGS["base_currency"]


def set_base_currency(currency: str):
    """
    Set the application's base currency.
    """
    conn = get_db_connection()
    conn.execute(
        "INSERT OR REPLACE INTO app_settings (key, value) VALUES ('base_currency', ?)",
        (currency,),
    )
    conn.commit()
    conn.close()


def get_exchange_rates() -> dict[str, float]:
    """
    Get all stored exchange rates relative to the base currency.
    """
    conn = get_db_connection()
    rows = conn.execute("SELECT currency, rate FROM exchange_rates").fetchall()
    conn.close()
    if not rows:
        print("[Warning] Exchange rates not found, using defaults.")
        return DEFAULT_SETTINGS["exchange_rates"]
    return {row["currency"]: row["rate"] for row in rows}


def set_exchange_rates(rates: dict[str, float]):
    """
    Save all exchange rates.
    """
    conn = get_db_connection()
    rate_list = list(rates.items())
    conn.executemany(
        "INSERT OR REPLACE INTO exchange_rates (currency, rate) VALUES (?, ?)",
        rate_list,
    )
    conn.commit()
    conn.close()
