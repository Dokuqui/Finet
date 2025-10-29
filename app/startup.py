from app.db.connection import init_db
from app.db.recurring import generate_due_transactions


def initialize(database_path: str):
    """
    Initializes the application, starting with the database.
    """
    init_db(database_path)

    created = generate_due_transactions()
    if created:
        print(f"[recurring] Generated {created} pending recurring transactions.")
