from .connection import get_db_connection
from app.models import Transaction


def add_transaction(date, amount, category_id, account_id, notes, currency):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO transactions (date, amount, category_id, account_id, notes, currency) VALUES (?, ?, ?, ?, ?, ?)",
        (date, amount, category_id, account_id, notes, currency),
    )
    conn.commit()
    conn.close()


def get_recent_transactions(limit=10):
    conn = get_db_connection()
    transactions = conn.execute(
        """
        SELECT t.*, c.name as category_name, c.icon as category_icon
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.date DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [Transaction.from_row(tx) for tx in transactions]


def delete_transaction(transaction_id):
    conn = get_db_connection()
    tx = conn.execute(
        "SELECT amount, account_id, currency, category_id FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()
    if tx:
        amount = tx["amount"]
        account_id = tx["account_id"]
        currency = tx["currency"]
        category_id = tx["category_id"]
        cat = conn.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()
        category_name = cat["name"] if cat else ""
        delta = -amount if category_name == "Salary" else amount
        conn.execute(
            "UPDATE account_balances SET balance = balance + ? WHERE account_id = ? AND currency = ?",
            (delta, account_id, currency)
        )
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()