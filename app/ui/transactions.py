import datetime
import flet as ft
from app.db import add_transaction, get_recent_transactions, delete_transaction

CATEGORIES = ["Food", "Transport", "Bills", "Salary", "Other"]
CATEGORY_ICONS = {"Food": ft.Icons.LUNCH_DINING, "Transport": ft.Icons.DIRECTIONS_BUS, "Bills": ft.Icons.RECEIPT, "Salary": ft.Icons.SAVINGS, "Other": ft.Icons.CATEGORY}
ACCOUNTS = ["Cash", "Bank", "Credit Card"]
ACCOUNT_ICONS = {"Cash": ft.Icons.MONEY, "Bank": ft.Icons.ACCOUNT_BALANCE, "Credit Card": ft.Icons.CREDIT_CARD}
CURRENCIES = ["USD", "EUR", "GBP"]

def transactions_page(page: ft.Page):
    selected_date = ft.Text("")
    currency_field = ft.Dropdown(label="Currency", value="USD", options=[ft.dropdown.Option(c) for c in CURRENCIES], width=100)
    amount_field = ft.TextField(label="Amount", value="0.00", keyboard_type="number", width=120)
    category_field = ft.Dropdown(label="Category", options=[ft.dropdown.Option(c) for c in CATEGORIES], width=150)
    account_field = ft.Dropdown(label="Account", options=[ft.dropdown.Option(a) for a in ACCOUNTS], width=150)
    notes_field = ft.TextField(label="Notes", value="", width=320)
    transaction_list = ft.Column(spacing=20)

    selected_date_value = ""

    # Date picker logic
    def handle_change(e):
        nonlocal selected_date_value
        try:
            selected_date_value = e.data.strftime("%Y-%m-%d")
        except Exception:
            selected_date_value = str(e.data)[:10]
        selected_date.value = selected_date_value
        page.update()

    def handle_dismissal(e):
        page.snack_bar = ft.SnackBar(ft.Text("Date selection dismissed."))
        page.update()

    date_picker = ft.DatePicker(
        first_date=datetime.date(year=2025, month=1, day=1),
        last_date=datetime.date(year=2035, month=12, day=1),
        on_change=handle_change,
        on_dismiss=handle_dismissal
    )
    date_btn = ft.ElevatedButton("Pick date", icon=ft.Icons.CALENDAR_MONTH, on_click=lambda e: page.open(date_picker))
    page.overlay.append(date_picker)

    def change_amount(delta):
        try:
            amt = float(amount_field.value)
        except ValueError:
            amt = 0.00
        amt += delta
        amount_field.value = f"{max(amt,0):.2f}"
        page.update()

    less_btn = ft.IconButton(icon=ft.Icons.REMOVE, on_click=lambda _: change_amount(-1))
    more_btn = ft.IconButton(icon=ft.Icons.ADD, on_click=lambda _: change_amount(1))

    def refresh_transactions(e=None):
        txs = get_recent_transactions()
        transaction_list.controls.clear()
        transaction_list.controls.append(
            ft.Text("Recent Transactions:", style="titleMedium", size=18, weight=ft.FontWeight.BOLD)
        )
        if not txs:
            transaction_list.controls.append(
                ft.Container(
                    ft.Text("No transactions found. Add your first transaction above!", italic=True),
                    padding=20,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8,
                )
            )
        else:
            for tx in txs:
                date_str = str(tx['date'])[:10]
                color = ft.Colors.GREEN_400 if tx['category'] == "Salary" else ft.Colors.RED_400 if tx['category'] in ["Food", "Bills", "Transport"] else ft.Colors.BLUE_400
                transaction_card = ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Row([
                                    ft.Icon(CATEGORY_ICONS.get(tx['category'], ft.Icons.CATEGORY), color=ft.Colors.BLUE_400),
                                    ft.Text(f"{tx['category']}", style="titleSmall"),
                                    ft.Icon(ACCOUNT_ICONS.get(tx['account'], ft.Icons.ACCOUNT_BALANCE), color=ft.Colors.GREY_700),
                                    ft.Text(f"{tx['account']}", style="bodyMedium"),
                                ], spacing=10),
                                ft.Text(f"Date: {date_str}", style="bodyMedium", color=ft.Colors.GREY_700),
                                ft.Text(f"Amount: {tx.get('currency', 'USD')} {tx['amount']:.2f}", style="titleMedium", color=color),
                                ft.Text(f"Notes: {tx['notes']}", style="bodyMedium", color=ft.Colors.GREY_700),
                            ], spacing=6),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Delete",
                                on_click=lambda e, txid=tx['id']: on_delete_click(txid),
                                style=ft.ButtonStyle(color=ft.Colors.RED_400, bgcolor=ft.Colors.GREY_100, shape=ft.RoundedRectangleBorder(radius=20)),
                                width=40,
                                height=40,
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=16,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=12,
                        shadow=ft.BoxShadow(
                            spread_radius=2,
                            blur_radius=6,
                            color=ft.Colors.GREY_300,
                            offset=ft.Offset(0, 2)
                        ),
                    ),
                    elevation=0,
                )
                transaction_list.controls.append(transaction_card)
        page.update()

    def on_add_click(e):
        date_val = selected_date.value or datetime.date.today().strftime("%Y-%m-%d")
        try:
            amt = float(amount_field.value)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter a valid amount."))
            page.update()
            return

        add_transaction(
            date_val,
            amt,
            category_field.value or "",
            account_field.value or "",
            notes_field.value,
            currency_field.value or "USD"
        )

        selected_date.value = ""
        amount_field.value = "0.00"
        category_field.value = None
        account_field.value = None
        notes_field.value = ""
        currency_field.value = "USD"
        page.snack_bar = ft.SnackBar(ft.Text("Transaction added!"))
        refresh_transactions()

    def on_delete_click(txid):
        delete_transaction(txid)
        page.snack_bar = ft.SnackBar(ft.Text("Transaction deleted!"))
        refresh_transactions()

    add_button = ft.ElevatedButton(
        "Add Transaction",
        on_click=on_add_click,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_400,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding(16, 6, 16, 6),
            elevation=2,
        ),
        width=200,
        height=40,
    )

    refresh_transactions()

    form = ft.Container(
        ft.Column(
            [
                ft.Text("Add Transaction", style="headlineSmall", size=26, weight=ft.FontWeight.BOLD),
                ft.Row([date_btn, selected_date], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
                ft.Row([amount_field, less_btn, more_btn, currency_field], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
                ft.Row([category_field, account_field], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
                notes_field,
                ft.Container(add_button, alignment=ft.alignment.center, margin=ft.margin.only(top=25)),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=18,
        ),
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.GREY_50,
        border_radius=14,
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=12,
            color=ft.Colors.GREY_200,
            offset=ft.Offset(0, 6)
        ),
        padding=ft.padding.all(32),
        margin=ft.margin.only(top=32, bottom=12),
        width=500,
    )

    return ft.Container(
        content=ft.Column([
            form,
            ft.Divider(),
            ft.Container(transaction_list, alignment=ft.alignment.center, padding=ft.padding.only(top=24, bottom=24), width=700),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll="auto",
        ),
        expand=True,
        alignment=ft.alignment.top_center,
    )
