import datetime
import flet as ft
from app.db.transactions import (
    add_transaction,
    get_recent_transactions,
    delete_transaction,
)
from app.db.accounts import get_accounts, increment_account_balance

CATEGORIES = ["Food", "Transport", "Bills", "Salary", "Other"]
CATEGORY_ICONS = {
    "Food": ft.Icons.LUNCH_DINING,
    "Transport": ft.Icons.DIRECTIONS_BUS,
    "Bills": ft.Icons.RECEIPT,
    "Salary": ft.Icons.SAVINGS,
    "Other": ft.Icons.CATEGORY,
}


def transactions_page(page: ft.Page):
    selected_date = ft.Text("")
    amount_field = ft.TextField(
        label="Amount",
        value="0.00",
        keyboard_type="number",
        width=120,
        border_color=ft.Colors.GREY_400,
        border_radius=8,
    )
    category_field = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(c) for c in CATEGORIES],
        width=160,
        border_radius=8,
        border_color=ft.Colors.GREY_400,
    )
    notes_field = ft.TextField(
        label="Notes",
        value="",
        width=335,
        border_color=ft.Colors.GREY_400,
        border_radius=8,
    )
    transaction_list = ft.Column(spacing=20)
    selected_date_value = ""

    accounts = get_accounts()
    account_field = ft.Dropdown(
        label="Account",
        width=210,
        border_radius=8,
        border_color=ft.Colors.GREY_400,
        options=[
            ft.dropdown.Option(str(acc.id), f"{acc.name} ({acc.type})")
            for acc in accounts
        ],
    )
    currency_field = ft.Dropdown(
        label="Currency",
        options=[],
        width=85,
        border_radius=8,
        border_color=ft.Colors.GREY_400,
    )

    def on_account_change(e):
        acc_id = int(account_field.value) if account_field.value else None
        acc = next((a for a in accounts if a.id == acc_id), None)
        if acc:
            currency_field.options = [
                ft.dropdown.Option(b["currency"]) for b in acc.balances
            ]
            if acc.balances:
                currency_field.value = acc.balances[0]["currency"]
            else:
                currency_field.value = None
            page.update()

    account_field.on_change = on_account_change

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
        on_dismiss=handle_dismissal,
    )
    date_btn = ft.ElevatedButton(
        "Pick date",
        icon=ft.Icons.CALENDAR_MONTH,
        on_click=lambda e: page.open(date_picker),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREY_100,
            color=ft.Colors.BLUE_400,
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.Padding(10, 5, 10, 5),
        ),
        width=120,
        height=36,
    )
    page.overlay.append(date_picker)

    def change_amount(delta):
        try:
            amt = float(amount_field.value)
        except ValueError:
            amt = 0.00
        amt += delta
        amount_field.value = f"{max(amt, 0):.2f}"
        page.update()

    less_btn = ft.IconButton(
        icon=ft.Icons.REMOVE,
        on_click=lambda _: change_amount(-1),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREY_100,
            color=ft.Colors.BLUE_400,
            shape=ft.RoundedRectangleBorder(radius=20),
        ),
        width=36,
        height=36,
    )
    more_btn = ft.IconButton(
        icon=ft.Icons.ADD,
        on_click=lambda _: change_amount(1),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREY_100,
            color=ft.Colors.BLUE_400,
            shape=ft.RoundedRectangleBorder(radius=20),
        ),
        width=36,
        height=36,
    )

    def refresh_transactions(e=None):
        txs = get_recent_transactions()
        transaction_list.controls.clear()
        transaction_list.controls.append(
            ft.Text(
                "Recent Transactions:",
                style="titleMedium",
                size=18,
                weight=ft.FontWeight.BOLD,
            )
        )
        if not txs:
            transaction_list.controls.append(
                ft.Container(
                    ft.Text(
                        "No transactions found. Add your first transaction above!",
                        italic=True,
                        color=ft.Colors.GREY_600,
                    ),
                    padding=18,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=10,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=8, bottom=8),
                )
            )
        else:
            for tx in txs:
                date_str = str(tx.date)[:10]
                color = (
                    ft.Colors.GREEN_400
                    if tx.category == "Salary"
                    else ft.Colors.RED_400
                    if tx.category in ["Food", "Bills", "Transport"]
                    else ft.Colors.BLUE_400
                )
                transaction_card = ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(
                                                    CATEGORY_ICONS.get(
                                                        tx.category,
                                                        ft.Icons.CATEGORY,
                                                    ),
                                                    color=color,
                                                ),
                                                ft.Text(
                                                    f"{tx.category}",
                                                    style="titleSmall",
                                                    weight=ft.FontWeight.BOLD,
                                                    color=ft.Colors.GREY_800,
                                                ),
                                                ft.Text(
                                                    f"Account: {tx.account_id}",
                                                    style="bodyMedium",
                                                    color=ft.Colors.GREY_600,
                                                ),
                                                ft.Text(
                                                    f"{tx.currency}",
                                                    style="bodyMedium",
                                                    color=ft.Colors.GREY_600,
                                                ),
                                            ],
                                            spacing=12,
                                        ),
                                        ft.Text(
                                            f"Date: {date_str}",
                                            style="bodyMedium",
                                            color=ft.Colors.GREY_700,
                                        ),
                                        ft.Text(
                                            f"Amount: {tx.currency} {tx.amount:.2f}",
                                            style="titleMedium",
                                            color=color,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            f"Notes: {tx.notes}",
                                            style="bodyMedium",
                                            color=ft.Colors.GREY_700,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Delete",
                                    on_click=lambda e, txid=tx.id: on_delete_click(
                                        txid
                                    ),
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.RED_400,
                                        bgcolor=ft.Colors.GREY_100,
                                        shape=ft.RoundedRectangleBorder(radius=18),
                                    ),
                                    width=38,
                                    height=38,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=14,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=12,
                        shadow=ft.BoxShadow(
                            spread_radius=2,
                            blur_radius=7,
                            color=ft.Colors.GREY_200,
                            offset=ft.Offset(0, 2),
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

        acc_id = int(account_field.value) if account_field.value else None
        currency = currency_field.value
        category = category_field.value or ""

        add_transaction(
            date_val,
            amt,
            category,
            acc_id,
            notes_field.value,
            currency,
        )

        delta = amt if category == "Salary" else -amt
        increment_account_balance(acc_id, currency, delta)

        selected_date.value = ""
        amount_field.value = "0.00"
        category_field.value = None
        account_field.value = None
        currency_field.value = None
        notes_field.value = ""
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
            shape=ft.RoundedRectangleBorder(radius=22),
            padding=ft.Padding(16, 10, 16, 10),
            elevation=2,
        ),
        width=210,
        height=44,
    )

    refresh_transactions()

    form = ft.Container(
        ft.Column(
            [
                ft.Text(
                    "Add Transaction",
                    style="headlineSmall",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                ft.Row(
                    [date_btn, selected_date],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                ),
                ft.Row(
                    [amount_field, less_btn, more_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                ),
                ft.Row(
                    [category_field, account_field, currency_field],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                ),
                notes_field,
                ft.Container(
                    add_button,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=30),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=22,
        ),
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.WHITE,
        border_radius=22,
        shadow=ft.BoxShadow(
            spread_radius=3,
            blur_radius=18,
            color=ft.Colors.GREY_100,
            offset=ft.Offset(0, 8),
        ),
        padding=ft.padding.all(38),
        margin=ft.margin.only(top=38, bottom=16),
        width=720,
    )

    return ft.Container(
        content=ft.Column(
            [
                form,
                ft.Divider(color=ft.Colors.GREY_100, height=2),
                ft.Container(
                    transaction_list,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=32, bottom=28),
                    width=700,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll="auto",
        ),
        expand=True,
        alignment=ft.alignment.top_center,
        bgcolor=ft.Colors.GREY_50,
    )
