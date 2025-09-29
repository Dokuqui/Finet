class Transaction:
    def __init__(self, date, amount, category, account, notes, currency):
        self.date = date
        self.amount = amount
        self.category = category
        self.account = account
        self.notes = notes
        self.currency = currency