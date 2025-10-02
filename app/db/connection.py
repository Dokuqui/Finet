import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "finet.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            notes TEXT
        )
    """)
    # Account balances table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            currency TEXT NOT NULL,
            balance REAL DEFAULT 0,
            UNIQUE(account_id, currency),
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """)
    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT DEFAULT 'Other'
        )
    """)
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category_id INTEGER,
            account_id INTEGER,
            notes TEXT,
            currency TEXT DEFAULT 'USD',
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    # Budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            period TEXT NOT NULL,           -- 'monthly' or 'weekly'
            amount REAL NOT NULL,
            start_date TEXT NOT NULL,       -- ISO format string
            end_date TEXT NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    """)
    # Migrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def apply_migration(migration_name, sql):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM migrations WHERE migration=?", (migration_name,)
    )
    if cursor.fetchone()[0] == 0:
        cursor.executescript(sql)
        cursor.execute(
            "INSERT INTO migrations (migration, applied_at) VALUES (?, datetime('now'))",
            (migration_name,),
        )
        conn.commit()
    conn.close()
