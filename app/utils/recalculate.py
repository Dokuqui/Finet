from app.db.connection import get_db_connection
from app.services.converter import get_conversion_rates, convert_to_base


def recalculate_all_conversions() -> (int, int): # type: ignore
    """
    Updates all historical transactions and recurring patterns with
    the latest exchange rates saved in the settings.

    Returns: (transactions_updated, recurring_updated)
    """
    conn = get_db_connection()
    rates = get_conversion_rates()

    tx_rows = conn.execute("SELECT id, amount, currency FROM transactions").fetchall()
    tx_to_update = []
    for row in tx_rows:
        converted_amount = convert_to_base(row["amount"], row["currency"], rates)
        tx_to_update.append((converted_amount, row["id"]))

    conn.executemany(
        "UPDATE transactions SET amount_converted = ? WHERE id = ?", tx_to_update
    )

    rec_rows = conn.execute(
        "SELECT id, amount, currency FROM recurring_transactions"
    ).fetchall()
    rec_to_update = []
    for row in rec_rows:
        converted_amount = convert_to_base(row["amount"], row["currency"], rates)
        rec_to_update.append((converted_amount, row["id"]))

    conn.executemany(
        "UPDATE recurring_transactions SET amount_converted = ? WHERE id = ?",
        rec_to_update,
    )

    conn.commit()
    conn.close()

    return (len(tx_to_update), len(rec_to_update))
