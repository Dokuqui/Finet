EXAMPLE_CSV_HEADER = "date,amount,category,account_id,notes,currency"
EXAMPLE_CSV_ROWS = """
2025-10-28,-25.50,Food,1,Groceries for the week,EUR
2025-10-27,3200.00,Salary,2,November Paycheck,EUR
2025-10-26,-8.75,Transport,1,Train ticket home,EUR
2025-10-25,-55.00,Shopping,3,"New shoes",USD
"""
EXAMPLE_CSV_FULL = EXAMPLE_CSV_HEADER + EXAMPLE_CSV_ROWS

EXAMPLE_CSV_EXPLANATIONS = """
**CSV Columns for Import:**

* **`date`** (Required): Transaction date in `YYYY-MM-DD` format.
* **`amount`** (Required): Transaction amount. **Use negative (-) for expenses and positive (+) for income.**
* **`category`** (Required): Exact name of an existing category in Finet (case-insensitive check). Unknown categories map to "Other".
* **`account_id`** (Required): The numeric ID of an existing account in Finet. You can use `account` as the header too.
* **`notes`** (Optional): Any text notes for the transaction.
* **`currency`** (Required): The 3-letter code (e.g., EUR, USD) of an active currency in Finet settings.
"""
