from .connection import get_db_connection


def add_category(name, icon="Other"):
    conn = get_db_connection()
    conn.execute("INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))
    conn.commit()
    conn.close()


def get_categories():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name, icon FROM categories ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_category(category_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


def update_category(category_id, name, icon="Other"):
    conn = get_db_connection()
    conn.execute(
        "UPDATE categories SET name = ?, icon = ? WHERE id = ?",
        (name, icon, category_id),
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
