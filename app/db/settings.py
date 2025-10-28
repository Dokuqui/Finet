import sqlite3
from typing import List
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
    return row["value"] if row else DEFAULT_SETTINGS["base_currency"]


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
    return (
        {row["currency"]: row["rate"] for row in rows}
        if rows
        else DEFAULT_SETTINGS["exchange_rates"]
    )


def set_exchange_rates(rates: dict[str, float]):
    base = get_base_currency()
    rates[base] = 1.0
    conn = get_db_connection()
    rate_list = list(rates.items())
    conn.executemany(
        "INSERT OR REPLACE INTO exchange_rates (currency, rate) VALUES (?, ?)",
        rate_list,
    )
    conn.commit()
    conn.close()


def get_active_currencies() -> List[dict]:
    """Returns a list of active currencies like [{'code': 'USD', 'name': '...', 'symbol': '$'}, ...]"""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT code, name, symbol FROM currencies ORDER BY code ASC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_currency(code: str, name: str, symbol: str | None):
    """Adds a new currency to the list of available currencies."""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO currencies (code, name, symbol) VALUES (?, ?, ?)",
            (code.upper(), name, symbol),
        )
        base = get_base_currency()
        default_rate = 1.0 if code.upper() == base else 1.0
        conn.execute(
            "INSERT OR IGNORE INTO exchange_rates (currency, rate) VALUES (?, ?)",
            (code.upper(), default_rate),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"Currency code '{code.upper()}' already exists.")
    finally:
        conn.close()


def delete_currency(code: str):
    """Removes a currency. Also removes its exchange rate."""
    conn = get_db_connection()
    base = get_base_currency()
    if code.upper() == base:
        conn.close()
        raise ValueError("Cannot delete the base currency.")

    cur = conn.execute(
        "SELECT 1 FROM account_balances WHERE currency = ? LIMIT 1", (code.upper(),)
    )
    if cur.fetchone():
        conn.close()
        raise ValueError(
            f"Cannot delete currency '{code.upper()}' as it is used in account balances."
        )

    conn.execute("DELETE FROM currencies WHERE code = ?", (code.upper(),))
    conn.execute("DELETE FROM exchange_rates WHERE currency = ?", (code.upper(),))
    conn.commit()
    conn.close()


def update_currency_symbol(code: str, symbol: str | None):
    """Updates the symbol for a currency."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE currencies SET symbol = ? WHERE code = ?", (symbol, code.upper())
    )
    conn.commit()
    conn.close()
