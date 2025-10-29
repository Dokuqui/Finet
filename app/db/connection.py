import sqlite3
import datetime
from app.services.currency_info import PREDEFINED_CURRENCIES

_DB_PATH = None


def get_db_path():
    """
    Returns the initialized database path.
    Raises an error if init_db() has not been called.
    """
    if _DB_PATH is None:
        raise ValueError(
            "Database path has not been initialized. Call init_db() from main.py first."
        )
    return _DB_PATH


def get_db_connection():
    """
    Gets a new database connection using the path
    set by init_db().
    """
    if _DB_PATH is None:
        raise ValueError(
            "Database path has not been initialized. Call init_db() from main.py first."
        )

    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(database_path: str):
    """
    Initializes the database path and creates/upgrades all tables.
    This MUST be called by startup.py before get_db_connection() is used.
    """
    global _DB_PATH
    _DB_PATH = database_path

    print(f"[DB] Database path set to: {_DB_PATH}")

    try:
        with get_db_connection() as conn:
            print("[DB] Database connection verified. Initializing schema...")

            _create_base_tables(conn)
            _init_settings_table(conn)
            _ensure_categories_type_column(conn)
            _ensure_balances_threshold_column(conn)
            _ensure_transactions_converted_column(conn)
            _ensure_recurring_table(conn)
            _ensure_recurring_columns(conn)
            _ensure_transactions_indexes(conn)

            conn.commit()

        print(
            "[schema] Database initialized / upgraded at",
            datetime.datetime.utcnow().isoformat(),
        )
    except Exception as e:
        print(f"[DB] Error during database initialization: {e}")
        raise


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


def _init_settings_table(conn):
    """
    Creates the settings tables if they don't exist.
    (Moved from settings.py to break circular import)
    """
    from app.db.settings import DEFAULT_SETTINGS

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY NOT NULL,
            value TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rates (
            currency TEXT PRIMARY KEY NOT NULL,
            rate REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS currencies (
            code TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            symbol TEXT
        )
    """)

    cur = conn.execute("SELECT 1 FROM app_settings WHERE key='base_currency'")
    if cur.fetchone() is None:
        conn.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?)",
            ("base_currency", DEFAULT_SETTINGS["base_currency"]),
        )

    cur = conn.execute("SELECT COUNT(*) FROM currencies")
    if cur.fetchone()[0] == 0:
        initial_currencies = [
            (code, name, symbol) for code, name, symbol in PREDEFINED_CURRENCIES
        ]
        conn.executemany(
            "INSERT INTO currencies (code, name, symbol) VALUES (?, ?, ?)",
            initial_currencies,
        )

        initial_rates = []
        default_rates = DEFAULT_SETTINGS["exchange_rates"]
        for code, name, symbol in PREDEFINED_CURRENCIES:
            if code in default_rates:
                initial_rates.append((code, default_rates[code]))
            elif code == DEFAULT_SETTINGS["base_currency"]:
                initial_rates.append((code, 1.0))

        if initial_rates:
            conn.executemany(
                "INSERT OR IGNORE INTO exchange_rates (currency, rate) VALUES (?, ?)",
                initial_rates,
            )


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
            balance_threshold REAL,
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
    # Transactions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            amount_converted REAL NOT NULL DEFAULT 0,
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
    if not _column_exists(conn, "categories", "type"):
        try:
            conn.execute(
                "ALTER TABLE categories ADD COLUMN type TEXT NOT NULL DEFAULT 'expense'"
            )
        except sqlite3.OperationalError:
            pass


def _ensure_balances_threshold_column(conn):
    if not _column_exists(conn, "account_balances", "balance_threshold"):
        try:
            conn.execute(
                "ALTER TABLE account_balances ADD COLUMN balance_threshold REAL"
            )
        except sqlite3.OperationalError:
            pass


def _ensure_transactions_converted_column(conn):
    if not _column_exists(conn, "transactions", "amount_converted"):
        try:
            conn.execute(
                "ALTER TABLE transactions ADD COLUMN amount_converted REAL NOT NULL DEFAULT 0"
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
                amount_converted REAL NOT NULL DEFAULT 0,
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
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_recurring_active_next
        ON recurring_transactions(active, next_occurrence)
    """)


def _ensure_recurring_columns(conn):
    add_cols = {
        "next_occurrence": "TEXT",
        "last_generated_at": "TEXT",
        "active": "INTEGER NOT NULL DEFAULT 1",
        "created_at": "TEXT",
        "updated_at": "TEXT",
        "amount_converted": "REAL NOT NULL DEFAULT 0",
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
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_recurring_unique
        ON transactions(recurring_id, occurrence_date)
        WHERE recurring_id IS NOT NULL
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_recurring
        ON transactions(recurring_id)
    """)
