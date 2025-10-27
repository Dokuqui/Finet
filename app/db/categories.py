from .connection import get_db_connection


def add_category(name, icon="Other", type="expense"):
    """
    Add a new category, specifying its type ('expense' or 'income').
    """
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO categories (name, icon, type) VALUES (?, ?, ?)", (name, icon, type)
    )
    conn.commit()
    conn.close()


def get_categories():
    """
    Get all categories, including their type.
    """
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name, icon, type FROM categories ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_category(category_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


def update_category(category_id, name, icon="Other", type="expense"):
    """
    Update a category, including its type.
    """
    conn = get_db_connection()
    conn.execute(
        "UPDATE categories SET name = ?, icon = ?, type = ? WHERE id = ?",
        (name, icon, type, category_id),
    )
    conn.commit()
    conn.close()


def get_category_id_by_name(name):
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone()
    conn.close()
    if row:
        return row["id"] if "id" in row.keys() else row[0]
    return None
