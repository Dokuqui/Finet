import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "finet.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------- Schema helpers ----------


def _table_exists(conn, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cur.fetchone() is not None


def _column_exists(conn, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def _create_base_tables(conn):
    # Accounts
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            notes TEXT
        )
    """)
    # Account balances
    conn.execute("""
        CREATE TABLE IF NOT EXISTS account_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            currency TEXT NOT NULL,
            balance REAL DEFAULT 0,
            balance_threshold REAL, -- ADDED: For low balance alerts
            UNIQUE(account_id, currency),
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """)
    # Categories
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT DEFAULT 'Other',
            type TEXT NOT NULL DEFAULT 'expense'
        )
    """)
    # Transactions (initial base schema)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category_id INTEGER,
            account_id INTEGER,
            notes TEXT,
            currency TEXT DEFAULT 'USD',
            recurring_id INTEGER,
            occurrence_date TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    # Budgets
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            period TEXT NOT NULL,
            amount REAL NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    """)


def _ensure_categories_type_column(conn):
    """
    Migration: Add the 'type' column to categories if it doesn't exist.
    """
    if not _column_exists(conn, "categories", "type"):
        try:
            conn.execute(
                "ALTER TABLE categories ADD COLUMN type TEXT NOT NULL DEFAULT 'expense'"
            )
        except sqlite3.OperationalError:
            pass


def _ensure_balances_threshold_column(conn):
    """
    Migration: Add the 'balance_threshold' column to account_balances.
    """
    if not _column_exists(conn, "account_balances", "balance_threshold"):
        try:
            conn.execute(
                "ALTER TABLE account_balances ADD COLUMN balance_threshold REAL"
            )
        except sqlite3.OperationalError:
            pass


def _ensure_recurring_table(conn):
    if not _table_exists(conn, "recurring_transactions"):
        conn.execute("""
            CREATE TABLE recurring_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                frequency TEXT NOT NULL,
                interval INTEGER,
                day_of_month INTEGER,
                weekday INTEGER,
                start_date TEXT NOT NULL,
                end_date TEXT,
                next_occurrence TEXT NOT NULL,
                last_generated_at TEXT,
                notes TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        """)
    # Indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_recurring_active_next
        ON recurring_transactions(active, next_occurrence)
    """)


def _ensure_recurring_columns(conn):
    """
    Defensive additions if early versions lacked columns.
    """
    add_cols = {
        "next_occurrence": "TEXT",
        "last_generated_at": "TEXT",
        "active": "INTEGER NOT NULL DEFAULT 1",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }
    for col, col_def in add_cols.items():
        if not _column_exists(conn, "recurring_transactions", col):
            try:
                conn.execute(
                    f"ALTER TABLE recurring_transactions ADD COLUMN {col} {col_def}"
                )
            except sqlite3.OperationalError:
                pass


def _ensure_transactions_indexes(conn):
    # Unique index preventing duplicate recurring occurrences
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_recurring_unique
        ON transactions(recurring_id, occurrence_date)
        WHERE recurring_id IS NOT NULL
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_recurring
        ON transactions(recurring_id)
    """)


def init_db():
    conn = get_db_connection()
    _create_base_tables(conn)
    _ensure_categories_type_column(conn)
    _ensure_balances_threshold_column(conn)
    _ensure_recurring_table(conn)
    _ensure_recurring_columns(conn)
    _ensure_transactions_indexes(conn)
    conn.commit()
    conn.close()
    print(
        "[schema] Database initialized / upgraded at",
        datetime.datetime.utcnow().isoformat(),
    )
