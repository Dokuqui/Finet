from app.db.connection import init_db
from app.db.recurring import generate_due_transactions

def initialize():
    init_db()
    created = generate_due_transactions()
    if created:
        print(f"[recurring] Generated {created} pending recurring transactions.")