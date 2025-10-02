from .connection import get_db_connection


def add_budget(category_id, period, amount, start_date, end_date):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO budgets (category_id, period, amount, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
        (category_id, period, amount, start_date, end_date),
    )
    conn.commit()
    conn.close()


def get_budgets():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM budgets").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_budget(budget_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM budgets WHERE id=?", (budget_id,))
    conn.commit()
    conn.close()


def update_budget(
    budget_id,
    category_id=None,
    period=None,
    amount=None,
    start_date=None,
    end_date=None,
):
    conn = get_db_connection()
    query = "UPDATE budgets SET "
    params = []
    if category_id is not None:
        query += "category_id=?, "
        params.append(category_id)
    if period is not None:
        query += "period=?, "
        params.append(period)
    if amount is not None:
        query += "amount=?, "
        params.append(amount)
    if start_date is not None:
        query += "start_date=?, "
        params.append(start_date)
    if end_date is not None:
        query += "end_date=?, "
        params.append(end_date)
    query = query.rstrip(", ")
    query += " WHERE id=?"
    params.append(budget_id)
    conn.execute(query, tuple(params))
    conn.commit()
    conn.close()
