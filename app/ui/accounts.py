import flet as ft
from app.db.accounts import (
    get_accounts,
    add_account,
    add_account_balance,
    update_account,
    delete_account,
    delete_account_balance,
)

ACCOUNT_TYPES = ["Cash", "Bank", "Credit Card"]
CURRENCIES = ["USD", "EUR", "GBP"]


def accounts_page(page: ft.Page):
    accounts_list = ft.Column(spacing=22)

    name_field = ft.TextField(
        label="Account Name",
        width=210,
        border_radius=10,
        border_color=ft.Colors.GREY_400,
    )
    type_field = ft.Dropdown(
        label="Type",
        options=[ft.dropdown.Option(t) for t in ACCOUNT_TYPES],
        width=160,
        border_radius=10,
        border_color=ft.Colors.GREY_400,
    )
    notes_field = ft.TextField(
        label="Notes", width=290, border_radius=10, border_color=ft.Colors.GREY_400
    )
    balance_fields = [
        ft.TextField(
            label=f"Balance ({curr})",
            value="0.00",
            keyboard_type="number",
            width=110,
            border_radius=10,
            border_color=ft.Colors.GREY_400,
        )
        for curr in CURRENCIES
    ]

    # --- Edit Account Dialog ---
    edit_dialog = ft.AlertDialog(modal=True)
    edit_name_field = ft.TextField(label="Account Name", width=210)
    edit_type_field = ft.Dropdown(
        label="Type", options=[ft.dropdown.Option(t) for t in ACCOUNT_TYPES], width=160
    )
    edit_notes_field = ft.TextField(label="Notes", width=290)
    edit_balance_fields = [
        ft.TextField(label=f"Balance ({curr})", width=110) for curr in CURRENCIES
    ]
    edit_account_id = [None]  # Mutable container for account id

    def open_edit_dialog(acc):
        edit_account_id[0] = acc.id
        edit_name_field.value = acc.name
        edit_type_field.value = acc.type
        edit_notes_field.value = acc.notes
        for i, curr in enumerate(CURRENCIES):
            bal = next((b["balance"] for b in acc.balances if b["currency"] == curr), 0)
            edit_balance_fields[i].value = str(bal)
        page.dialog = edit_dialog
        edit_dialog.open = True
        page.update()

    def close_edit_dialog(e=None):
        edit_dialog.open = False
        page.update()

    def save_edit(e):
        update_account(
            edit_account_id[0],
            name=edit_name_field.value,
            type=edit_type_field.value or "Cash",
            notes=edit_notes_field.value,
        )
        for i, curr in enumerate(CURRENCIES):
            bal = float(edit_balance_fields[i].value or "0")
            add_account_balance(edit_account_id[0], curr, bal)
        close_edit_dialog()
        refresh_accounts()

    edit_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text(
                    "Edit Account",
                    style="headlineSmall",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),
                edit_name_field,
                edit_type_field,
                edit_notes_field,
                ft.Row(edit_balance_fields, spacing=10),
                ft.Row(
                    [
                        ft.ElevatedButton("Save", on_click=save_edit, width=120),
                        ft.ElevatedButton(
                            "Cancel",
                            on_click=close_edit_dialog,
                            bgcolor=ft.Colors.GREY_200,
                            color=ft.Colors.GREY_700,
                            width=120,
                        ),
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=16,
        ),
        width=420,
        padding=ft.padding.all(26),
        bgcolor=ft.Colors.WHITE,
        border_radius=18,
    )

    page.overlay.append(edit_dialog)

    # --- Transfer Money Dialog ---
    transfer_dialog = ft.AlertDialog(modal=True)
    transfer_from_field = ft.Dropdown(label="From Account", width=210)
    transfer_to_field = ft.Dropdown(label="To Account", width=210)
    transfer_currency_field = ft.Dropdown(label="Currency", width=110)
    transfer_amount_field = ft.TextField(label="Amount", width=110)

    def open_transfer_dialog(e=None):
        accts = get_accounts()
        transfer_from_field.options = [
            ft.dropdown.Option(str(a.id), a.name) for a in accts
        ]
        transfer_to_field.options = [
            ft.dropdown.Option(str(a.id), a.name) for a in accts
        ]
        transfer_currency_field.options = [ft.dropdown.Option(c) for c in CURRENCIES]
        transfer_from_field.value = None
        transfer_to_field.value = None
        transfer_currency_field.value = None
        transfer_amount_field.value = ""
        transfer_dialog.open = True
        page.dialog = transfer_dialog
        page.update()

    def close_transfer_dialog(e=None):
        transfer_dialog.open = False
        page.update()

    def confirm_transfer(e):
        from_id = int(transfer_from_field.value)
        to_id = int(transfer_to_field.value)
        currency = transfer_currency_field.value
        amount = float(transfer_amount_field.value)
        # Subtract from source
        add_account_balance(from_id, currency, -amount)
        # Add to destination
        add_account_balance(to_id, currency, amount)
        close_transfer_dialog()
        refresh_accounts()
        page.snack_bar = ft.SnackBar(ft.Text("Transfer complete!"))
        page.update()

    transfer_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text(
                    "Transfer Money",
                    style="headlineSmall",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),
                transfer_from_field,
                transfer_to_field,
                transfer_currency_field,
                transfer_amount_field,
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Transfer", on_click=confirm_transfer, width=120
                        ),
                        ft.ElevatedButton(
                            "Cancel",
                            on_click=close_transfer_dialog,
                            bgcolor=ft.Colors.GREY_200,
                            color=ft.Colors.GREY_700,
                            width=120,
                        ),
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=16,
        ),
        width=420,
        padding=ft.padding.all(26),
        bgcolor=ft.Colors.WHITE,
        border_radius=18,
    )

    page.overlay.append(transfer_dialog)

    # --- Account List and Controls ---
    def refresh_accounts():
        accounts_list.controls.clear()
        for acc in get_accounts():
            balances_str = ", ".join(
                [f"{b['currency']}: {b['balance']:.2f}" for b in acc.balances]
            )
            card = ft.Card(
                content=ft.Container(
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        acc.name,
                                        style="headlineSmall",
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREY_900,
                                    ),
                                    ft.Text(
                                        f"Type: {acc.type}",
                                        style="bodyMedium",
                                        color=ft.Colors.GREY_700,
                                    ),
                                    ft.Text(
                                        f"Balances: {balances_str}",
                                        style="bodyMedium",
                                        color=ft.Colors.GREY_800,
                                    ),
                                    ft.Text(
                                        f"Notes: {acc.notes}",
                                        style="bodySmall",
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                spacing=6,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Edit",
                                        on_click=lambda e, acc=acc: open_edit_dialog(
                                            acc
                                        ),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_50,
                                            color=ft.Colors.BLUE_400,
                                            shape=ft.RoundedRectangleBorder(radius=16),
                                        ),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Delete",
                                        on_click=lambda e,
                                        acc_id=acc.id: delete_account_ui(acc_id),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_50,
                                            color=ft.Colors.RED_400,
                                            shape=ft.RoundedRectangleBorder(radius=16),
                                        ),
                                        hover_color=ft.Colors.RED_100,
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=18,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=20,
                    shadow=ft.BoxShadow(
                        spread_radius=2,
                        blur_radius=16,
                        color=ft.Colors.GREY_100,
                        offset=ft.Offset(0, 6),
                    ),
                ),
                elevation=0,
            )
            accounts_list.controls.append(card)
        page.update()

    def add_account_ui(e):
        acc_id = add_account(
            name_field.value, type_field.value or "Cash", notes_field.value
        )
        for i, curr in enumerate(CURRENCIES):
            balance = float(balance_fields[i].value or "0")
            add_account_balance(acc_id, curr, balance)
            balance_fields[i].value = "0.00"
        name_field.value = ""
        type_field.value = None
        notes_field.value = ""
        refresh_accounts()

    def delete_account_ui(acc_id):
        delete_account(acc_id)
        refresh_accounts()

    add_btn = ft.ElevatedButton(
        "Add Account",
        on_click=add_account_ui,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_400,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=18),
            padding=ft.Padding(16, 10, 16, 10),
            elevation=2,
        ),
        width=180,
        height=44,
    )

    transfer_btn = ft.ElevatedButton(
        "Transfer Money",
        icon=ft.Icons.SWAP_HORIZ,
        on_click=open_transfer_dialog,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREEN_400,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=18),
            elevation=2,
        ),
        width=180,
        height=44,
    )

    refresh_accounts()

    form = ft.Container(
        ft.Column(
            [
                ft.Text(
                    "Add Account",
                    style="headlineSmall",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                ft.Row(
                    [name_field, type_field, notes_field],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                ),
                ft.Row(
                    balance_fields + [add_btn, transfer_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
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
        width=850,
    )

    return ft.Container(
        content=ft.Column(
            [
                form,
                ft.Divider(color=ft.Colors.GREY_100, height=2),
                ft.Container(
                    accounts_list,
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
