from .connection import get_db_connection
from app.models import Transaction


def add_transaction(date, amount, category, account_id, notes, currency):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO transactions (date, amount, category, account_id, notes, currency) VALUES (?, ?, ?, ?, ?, ?)",
        (date, amount, category, account_id, notes, currency),
    )
    conn.commit()
    conn.close()


def get_recent_transactions(limit=10):
    conn = get_db_connection()
    transactions = conn.execute(
        "SELECT * FROM transactions ORDER BY date DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [Transaction.from_row(tx) for tx in transactions]


def delete_transaction(transaction_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()
