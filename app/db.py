import sqlite3

def get_db_connection():
    conn = sqlite3.connect("finet.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            account TEXT,
            notes TEXT,
            currency TEXT DEFAULT 'USD'
        )
    """)
    conn.commit()
    conn.close()

def add_transaction(date, amount, category, account, notes, currency):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO transactions (date, amount, category, account, notes, currency) VALUES (?, ?, ?, ?, ?, ?)",
        (date, amount, category, account, notes, currency)
    )
    conn.commit()
    conn.close()

def get_recent_transactions(limit=10):
    conn = get_db_connection()
    transactions = conn.execute(
        "SELECT * FROM transactions ORDER BY date DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    print([dict(tx) for tx in transactions])
    return [dict(tx) for tx in transactions]

def delete_transaction(transaction_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()