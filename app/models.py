class Transaction:
    def __init__(self, id, date, amount, category, account_id, notes, currency):
        self.id = id
        self.date = date
        self.amount = amount
        self.category = category
        self.account_id = account_id
        self.notes = notes
        self.currency = currency

    @classmethod
    def from_row(cls, row):
        return cls(
            row["id"],
            row["date"],
            row["amount"],
            row["category"],
            row["account_id"],
            row["notes"],
            row["currency"],
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
