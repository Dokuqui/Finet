class Transaction:
    def __init__(
        self,
        id,
        date,
        amount,
        category_id,
        account_id,
        notes,
        currency,
        category_name=None,
        category_icon=None,
    ):
        self.id = id
        self.date = date
        self.amount = amount
        self.category_id = category_id
        self.account_id = account_id
        self.notes = notes
        self.currency = currency
        self.category_name = category_name
        self.category_icon = category_icon

    @classmethod
    def from_row(cls, row):
        return cls(
            row["id"],
            row["date"],
            row["amount"],
            row["category_id"],
            row["account_id"],
            row["notes"],
            row["currency"],
            row["category_name"] if "category_name" in row.keys() else None,
            row["category_icon"] if "category_icon" in row.keys() else "Other",
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
