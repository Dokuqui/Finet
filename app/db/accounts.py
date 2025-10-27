from .connection import get_db_connection
from app.models import Account


def add_account(name, type, notes=""):
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO accounts (name, type, notes) VALUES (?, ?, ?)", (name, type, notes)
    )
    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return account_id


def update_account(account_id, name=None, type=None, notes=None):
    conn = get_db_connection()
    query = "UPDATE accounts SET "
    params = []
    if name is not None:
        query += "name=?, "
        params.append(name)
    if type is not None:
        query += "type=?, "
        params.append(type)
    if notes is not None:
        query += "notes=?, "
        params.append(notes)
    query = query.rstrip(", ")
    query += " WHERE id=?"
    params.append(account_id)
    conn.execute(query, tuple(params))
    conn.commit()
    conn.close()


def delete_account(account_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.execute("DELETE FROM account_balances WHERE account_id = ?", (account_id,))
    conn.commit()
    conn.close()


def add_account_balance(account_id, currency, delta):
    conn = get_db_connection()
    # Check if exists
    row = conn.execute(
        "SELECT balance FROM account_balances WHERE account_id=? AND currency=?",
        (account_id, currency),
    ).fetchone()
    current = row["balance"] if row else 0.0
    new_balance = current + delta
    conn.execute(
        """
        INSERT INTO account_balances (account_id, currency, balance)
        VALUES (?, ?, ?)
        ON CONFLICT(account_id, currency) DO UPDATE SET balance=excluded.balance
        """,
        (account_id, currency, new_balance),
    )
    conn.commit()
    conn.close()


def set_account_balance_threshold(account_id, currency, threshold: float | None):
    """
    Set or clear the low-balance threshold for a specific currency on an account.
    """
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE account_balances
        SET balance_threshold = ?
        WHERE account_id = ? AND currency = ?
        """,
        (threshold, account_id, currency),
    )
    conn.commit()
    conn.close()


def update_account_balance(account_id, currency, balance):
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE account_balances
        SET balance=?
        WHERE account_id=? AND currency=?
    """,
        (balance, account_id, currency),
    )
    conn.commit()
    conn.close()


def get_account_balances(account_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT currency, balance, balance_threshold FROM account_balances WHERE account_id=?",
        (account_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_account_balance(account_id, currency):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM account_balances WHERE account_id=? AND currency=?",
        (account_id, currency),
    )
    conn.commit()
    conn.close()


def get_accounts():
    conn = get_db_connection()
    accounts = conn.execute("SELECT * FROM accounts").fetchall()
    results = []
    for acc in accounts:
        balances = conn.execute(
            "SELECT currency, balance, balance_threshold FROM account_balances WHERE account_id=?",
            (acc["id"],),
        ).fetchall()
        results.append(Account.from_row(acc, balances=[dict(b) for b in balances]))
    conn.close()
    return results


def get_low_balance_alerts():
    """
    Get all account balances that are below their set threshold.
    """
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            a.name AS account_name,
            ab.currency,
            ab.balance,
            ab.balance_threshold
        FROM account_balances ab
        JOIN accounts a ON ab.account_id = a.id
        WHERE
            ab.balance_threshold IS NOT NULL
            AND ab.balance < ab.balance_threshold
        ORDER BY a.name, ab.currency
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def increment_account_balance(account_id, currency, delta):
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE account_balances
        SET balance = balance + ?
        WHERE account_id = ? AND currency = ?
        """,
        (delta, account_id, currency),
    )
    conn.commit()
    conn.close()
