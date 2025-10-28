from dataclasses import dataclass


@dataclass
class Transaction:
    id: int
    date: str
    amount: float
    category_id: int | None
    account_id: int | None
    notes: str | None
    currency: str
    category_name: str | None = None
    category_icon: str | None = None
    recurring_id: int | None = None
    occurrence_date: str | None = None

    @classmethod
    def from_row(cls, row):
        def _get(r, key):
            try:
                return r[key]
            except Exception:
                return None

        return cls(
            id=_get(row, "id"),
            date=_get(row, "date"),
            amount=_get(row, "amount"),
            category_id=_get(row, "category_id"),
            account_id=_get(row, "account_id"),
            notes=_get(row, "notes"),
            currency=_get(row, "currency"),
            category_name=_get(row, "category_name"),
            category_icon=_get(row, "category_icon"),
            recurring_id=_get(row, "recurring_id"),
            occurrence_date=_get(row, "occurrence_date"),
        )


class Account:
    def __init__(self, id, name, type, notes, balances=None):
        self.id = id
        self.name = name
        self.type = type
        self.notes = notes
        self.balances = balances or []

    @classmethod
    def from_row(cls, row, balances=None):
        return cls(row["id"], row["name"], row["type"], row["notes"], balances or [])


class Budget:
    def __init__(self, id, category_id, period, amount, start_date, end_date):
        self.id = id
        self.category_id = category_id
        self.period = period
        self.amount = amount
        self.start_date = start_date
        self.end_date = end_date
