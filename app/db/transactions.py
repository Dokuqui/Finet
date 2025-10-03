from .connection import get_db_connection
from app.models import Transaction


def add_transaction(
    date,
    amount,
    category_id,
    account_id,
    notes,
    currency,
    recurring_id=None,
    occurrence_date=None,
):
    """
    Stores a transaction with SIGNED amount:
      - Income categories: positive amount
      - Expense categories: negative amount

    Account balances are adjusted outside this function to keep it pure.
    """
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO transactions
          (date, amount, category_id, account_id, notes, currency, recurring_id, occurrence_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            date,
            amount,
            category_id,
            account_id,
            notes,
            currency,
            recurring_id,
            occurrence_date,
        ),
    )
    conn.commit()
    conn.close()


def get_recent_transactions(limit=10):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT t.*,
               c.name AS category_name,
               c.icon AS category_icon
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.date DESC, t.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [Transaction.from_row(r) for r in rows]


def delete_transaction(transaction_id: int):
    """
    Deletes a transaction and reverses its balance impact.
    Since amounts are signed, we just subtract the stored amount from balance
    (equivalent to adding the negative).
    """
    conn = get_db_connection()
    tx = conn.execute(
        "SELECT amount, account_id, currency FROM transactions WHERE id = ?",
        (transaction_id,),
    ).fetchone()
    if tx:
        amount = tx["amount"]  # signed
        account_id = tx["account_id"]
        currency = tx["currency"]
        conn.execute(
            "UPDATE account_balances SET balance = balance - ? WHERE account_id = ? AND currency = ?",
            (amount, account_id, currency),
        )
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


def get_category_spend(category_id, start_date, end_date):
    """
    Returns net sum (signed) for category; callers decide how to interpret.
    """
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT SUM(amount) as total
        FROM transactions
        WHERE category_id = ? AND date >= ? AND date <= ?
        """,
        (category_id, start_date, end_date),
    ).fetchone()
    conn.close()
    return row["total"] if row and row["total"] else 0.0


def get_transactions_for_analytics():
    """
    Returns raw dict rows including signed amounts for analytics.
    """
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT id, date, amount, category_id, account_id, currency,
               recurring_id, occurrence_date
        FROM transactions
        ORDER BY date ASC, id ASC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
