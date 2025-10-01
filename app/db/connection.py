import sqlite3

DB_PATH = "finet.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    # Transaction table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            account_id INTEGER,
            notes TEXT,
            currency TEXT DEFAULT 'USD'
        )
    """)
    # Account table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            notes TEXT
        )
    """)
    # Multi-currency balances per account
    conn.execute("""
        CREATE TABLE IF NOT EXISTS account_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
            currency TEXT NOT NULL,
            balance REAL DEFAULT 0,
            UNIQUE(account_id, currency)
        )
    """)
    conn.commit()
    conn.close()
