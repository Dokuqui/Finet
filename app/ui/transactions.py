import datetime
import flet as ft
from app.db.transactions import (
    add_transaction,
    get_recent_transactions,
    delete_transaction,
)
from app.db.accounts import get_accounts, increment_account_balance
from app.db.categories import (
    get_categories,
    add_category,
    delete_category,
    update_category,
)

# Expanded icon choices
ICON_CHOICES = [
    {"name": "Food", "icon": ft.Icons.LUNCH_DINING},
    {"name": "Transport", "icon": ft.Icons.DIRECTIONS_BUS},
    {"name": "Bills", "icon": ft.Icons.RECEIPT},
    {"name": "Salary", "icon": ft.Icons.SAVINGS},
    {"name": "Shopping", "icon": ft.Icons.SHOPPING_CART},
    {"name": "Health", "icon": ft.Icons.HEALTH_AND_SAFETY},
    {"name": "Travel", "icon": ft.Icons.FLIGHT},
    {"name": "Home", "icon": ft.Icons.HOME},
    {"name": "Leisure", "icon": ft.Icons.SPORTS_ESPORTS},
    {"name": "Education", "icon": ft.Icons.SCHOOL},
    {"name": "Entertainment", "icon": ft.Icons.MOVIE},
    {"name": "Other", "icon": ft.Icons.CATEGORY},
]


def get_icon_by_name(name):
    return next(
        (ic["icon"] for ic in ICON_CHOICES if ic["name"] == name), ft.Icons.CATEGORY
    )


def transactions_page(page: ft.Page):
    add_dialog = ft.AlertDialog(modal=True)
    edit_dialog = ft.AlertDialog(modal=True)
    list_dialog = ft.AlertDialog(modal=True)

    add_name_field = ft.TextField(label="Category Name", width=200)
    add_icon_dropdown = ft.Dropdown(
        label="Icon",
        options=[ft.dropdown.Option(ic["name"]) for ic in ICON_CHOICES],
        value="Other",
        width=120,
    )
    add_icon_preview = ft.Icon(get_icon_by_name(add_icon_dropdown.value), size=32)
    add_feedback = ft.Text("", color=ft.Colors.RED_400, size=13)

    edit_name_field = ft.TextField(label="Category Name", width=200)
    edit_icon_dropdown = ft.Dropdown(
        label="Icon",
        options=[ft.dropdown.Option(ic["name"]) for ic in ICON_CHOICES],
        value="Other",
        width=120,
    )
    edit_icon_preview = ft.Icon(get_icon_by_name(edit_icon_dropdown.value), size=32)
    edit_feedback = ft.Text("", color=ft.Colors.RED_400, size=13)
    editing_id = [None]

    categories_list = ft.Column(spacing=10, scroll="auto")

    category_field = ft.Dropdown(
        label="",
        options=[],
        width=160,
        border_radius=8,
        border_color=ft.Colors.GREY_400,
    )

    def on_add_icon_change(e):
        add_icon_preview.name = get_icon_by_name(add_icon_dropdown.value)
        page.update()

    add_icon_dropdown.on_change = on_add_icon_change

    def on_edit_icon_change(e):
        edit_icon_preview.name = get_icon_by_name(edit_icon_dropdown.value)
        page.update()

    edit_icon_dropdown.on_change = on_edit_icon_change

    def open_add_dialog(e=None):
        add_name_field.value = ""
        add_icon_dropdown.value = "Other"
        add_icon_preview.name = get_icon_by_name("Other")
        add_feedback.value = ""
        add_dialog.open = True
        page.dialog = add_dialog
        page.update()

    def close_add_dialog(e=None):
        add_dialog.open = False
        page.update()

    def save_new_category(e):
        name = add_name_field.value.strip()
        icon = add_icon_dropdown.value
        if not name:
            add_feedback.value = "Name can't be empty"
            page.update()
            return
        try:
            add_category(name, icon)
            close_add_dialog()
            refresh_categories()
        except Exception as ex:
            add_feedback.value = f"Error: {ex}"
            page.update()

    add_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("Add Category", style="headlineSmall", size=18),
                add_name_field,
                ft.Row([add_icon_dropdown, add_icon_preview], spacing=10),
                ft.Row(
                    [
                        ft.ElevatedButton("Save", on_click=save_new_category, width=90),
                        ft.TextButton("Cancel", on_click=close_add_dialog, width=90),
                        add_feedback,
                    ],
                    spacing=10,
                ),
            ],
            spacing=14,
        ),
        width=260,
        padding=18,
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
    )
    page.overlay.append(add_dialog)

    def open_edit_dialog(cat):
        editing_id[0] = cat["id"]
        edit_name_field.value = cat["name"]
        edit_icon_dropdown.value = cat.get("icon") or "Other"
        edit_icon_preview.name = get_icon_by_name(edit_icon_dropdown.value)
        edit_feedback.value = ""
        edit_dialog.open = True
        page.dialog = edit_dialog
        page.update()

    def close_edit_dialog(e=None):
        edit_dialog.open = False
        page.update()

    def save_edit_category(e):
        name = edit_name_field.value.strip()
        icon = edit_icon_dropdown.value
        if not name:
            edit_feedback.value = "Name can't be empty"
            page.update()
            return
        try:
            update_category(editing_id[0], name, icon)
            close_edit_dialog()
            refresh_categories()
        except Exception as ex:
            edit_feedback.value = f"Error: {ex}"
            page.update()

    edit_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("Edit Category", style="headlineSmall", size=18),
                edit_name_field,
                ft.Row([edit_icon_dropdown, edit_icon_preview], spacing=10),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Save", on_click=save_edit_category, width=90
                        ),
                        ft.TextButton("Cancel", on_click=close_edit_dialog, width=90),
                        edit_feedback,
                    ],
                    spacing=10,
                ),
            ],
            spacing=14,
        ),
        width=260,
        padding=18,
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
    )
    page.overlay.append(edit_dialog)

    def open_list_dialog(e=None):
        refresh_categories_list()
        list_dialog.open = True
        page.dialog = list_dialog
        page.update()

    def close_list_dialog(e=None):
        list_dialog.open = False
        page.update()

    def refresh_categories_list():
        cats = get_categories()
        categories_list.controls.clear()
        for cat in cats:
            categories_list.controls.append(
                ft.Row(
                    [
                        ft.Icon(
                            get_icon_by_name(cat.get("icon", "Other")),
                            color=ft.Colors.BLUE_400,
                            size=20,
                        ),
                        ft.Text(cat["name"], style="bodyMedium", width=120),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            tooltip="Edit",
                            on_click=lambda e, cat=cat: open_edit_dialog(cat),
                            style=ft.ButtonStyle(
                                color=ft.Colors.BLUE_400,
                                bgcolor=ft.Colors.GREY_50,
                                shape=ft.RoundedRectangleBorder(radius=14),
                            ),
                            width=26,
                            height=26,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            tooltip="Delete",
                            on_click=lambda e, cat_id=cat["id"]: on_delete_cat(cat_id),
                            style=ft.ButtonStyle(
                                color=ft.Colors.RED_400,
                                bgcolor=ft.Colors.GREY_50,
                                shape=ft.RoundedRectangleBorder(radius=14),
                            ),
                            width=26,
                            height=26,
                        ),
                    ],
                    spacing=4,
                )
            )
        page.update()

    list_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("Categories", style="headlineSmall", size=18),
                categories_list,
                ft.Row(
                    [
                        ft.TextButton("Close", on_click=close_list_dialog, width=90),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=14,
        ),
        width=320,
        padding=18,
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
        height=320,
    )
    page.overlay.append(list_dialog)

    def on_delete_cat(cat_id):
        delete_category(cat_id)
        refresh_categories()
        refresh_categories_list()

    def refresh_categories():
        cats = get_categories()
        category_field.options = [
            ft.dropdown.Option(str(cat["id"]), cat["name"]) for cat in cats
        ]
        page.update()

    selected_date = ft.Text("")
    amount_field = ft.TextField(
        label="Amount",
        value="0.00",
        keyboard_type="number",
        width=120,
        border_color=ft.Colors.GREY_400,
        border_radius=8,
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
                category_name = tx.category_name or "Other"
                icon_name = getattr(tx, "category_icon", "Other")
                color = (
                    ft.Colors.GREEN_400
                    if category_name == "Salary"
                    else ft.Colors.RED_400
                    if category_name in ["Food", "Bills", "Transport"]
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
                                                    get_icon_by_name(icon_name),
                                                    color=color,
                                                ),
                                                ft.Text(
                                                    f"{category_name}",
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
        category_id = int(category_field.value) if category_field.value else None

        add_transaction(
            date_val,
            amt,
            category_id,
            acc_id,
            notes_field.value,
            currency,
        )

        cats_now = get_categories()
        category_name = next(
            (cat["name"] for cat in cats_now if cat["id"] == category_id), "Other"
        )
        delta = amt if category_name == "Salary" else -amt
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

    # --- UI layout ---
    list_category_btn = ft.IconButton(
        icon=ft.Icons.LIST,
        tooltip="Show Categories",
        on_click=open_list_dialog,
        style=ft.ButtonStyle(
            color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.GREY_50,
            shape=ft.RoundedRectangleBorder(radius=18),
        ),
        width=38,
        height=38,
    )
    
    add_category_btn = ft.ElevatedButton(
        "Add Category",
        icon=ft.Icons.ADD,
        on_click=open_add_dialog,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_400,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=14),
        ),
        width=135,
        height=38,
    )

    refresh_categories()
    refresh_transactions()
    
    category_controls_row = ft.Row(
        [add_category_btn, list_category_btn],
        alignment=ft.MainAxisAlignment.START,
        spacing=12,
    )
    
    category_controls_panel = ft.Container(
        content=category_controls_row,
        alignment=ft.alignment.center_left,
        padding=ft.padding.only(left=32, top=18, bottom=10),
        width=760,
    )

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
        margin=ft.margin.only(top=10, bottom=16),
        width=720,
    )

    return ft.Container(
        content=ft.Column(
            [
                category_controls_panel,
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
