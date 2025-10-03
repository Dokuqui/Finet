import flet as ft
from decimal import Decimal, InvalidOperation
from app.db.accounts import (
    get_accounts,
    add_account,
    add_account_balance,
    update_account,
    delete_account,
)

ACCOUNT_TYPES = ["Cash", "Bank", "Credit Card"]
ALL_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD"]


def accounts_page(page: ft.Page):
    # ---------- Theme-ish helpers ----------
    ACCENT = ft.Colors.BLUE_400
    SUCCESS = ft.Colors.GREEN_400
    DANGER = ft.Colors.RED_400
    WARNING = ft.Colors.AMBER_400
    SURFACE = ft.Colors.WHITE
    BG = ft.Colors.GREY_50
    BORDER = ft.Colors.GREY_300

    page.bgcolor = BG

    def parse_amount(v: str) -> float:
        if not v:
            return 0.0
        try:
            return float(Decimal(v))
        except (InvalidOperation, ValueError):
            return 0.0

    # ========== Shared dynamic currency row utilities ==========
    def selected_currencies(rows):
        return [r["currency"].value for r in rows if r["currency"].value]

    def available_currencies(rows, keep=None):
        picked = set(selected_currencies(rows))
        if keep:
            picked.discard(keep)  # allow its own current value
        return [c for c in ALL_CURRENCIES if c not in picked]

    def rebuild_currency_dropdown_options(rows, column):
        # Only rebuild if mounted
        if not column.page:
            return
        for r in rows:
            keep = r["currency"].value
            opts = available_currencies(rows, keep=keep)
            if keep and keep not in opts:
                opts.append(keep)
            r["currency"].options = [ft.dropdown.Option(c) for c in sorted(opts)]
        column.update()

    # Generic add/remove helpers
    def add_currency_row(
        rows,
        column,
        *,
        initial_currency=None,
        initial_amount="0.00",
        trigger_update=True,
    ):
        dd = ft.Dropdown(
            label="Currency",
            width=130,
            value=initial_currency,
            options=[
                ft.dropdown.Option(c)
                for c in sorted(available_currencies(rows, keep=initial_currency))
            ],
        )
        amt = ft.TextField(
            label="Amount",
            width=120,
            value=initial_amount,
            keyboard_type="number",
        )

        container_ref = ft.Ref[ft.Container]()

        def on_change_currency(e):
            rebuild_currency_dropdown_options(rows, column)

        dd.on_change = on_change_currency

        def remove_row(e):
            for entry in list(rows):
                if entry["container"] is container_ref.current:
                    rows.remove(entry)
            column.controls.remove(container_ref.current)
            rebuild_currency_dropdown_options(rows, column)

        remove_btn = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            tooltip="Remove",
            icon_size=18,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREY_100,
                color=ft.Colors.GREY_700,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=remove_row,
        )

        c = ft.Container(
            ref=container_ref,
            content=ft.Row([dd, amt, remove_btn], spacing=10),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border=ft.border.all(1, BORDER),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
        )

        rows.append({"currency": dd, "amount": amt, "container": c})
        column.controls.append(c)

        # Only rebuild/update if already attached to page (avoids assertion)
        if trigger_update and column.page:
            rebuild_currency_dropdown_options(rows, column)

    # ========== Add Account Section ==========
    name_field = ft.TextField(label="Account Name", width=240)
    type_field = ft.Dropdown(
        label="Type",
        width=170,
        options=[ft.dropdown.Option(t) for t in ACCOUNT_TYPES],
    )
    notes_field = ft.TextField(label="Notes", width=300)

    add_currency_rows = []
    add_currency_column = ft.Column(spacing=10, width=540)

    # initial row without update
    add_currency_row(add_currency_rows, add_currency_column, trigger_update=False)

    def clear_add_form():
        name_field.value = ""
        type_field.value = None
        notes_field.value = ""
        add_currency_rows.clear()
        add_currency_column.controls.clear()
        add_currency_row(add_currency_rows, add_currency_column, trigger_update=False)
        page.update()

    def add_account_ui(e):
        if not name_field.value.strip():
            snack("Account name required", WARNING)
            return
        acc_id = add_account(
            name_field.value.strip(),
            type_field.value or "Cash",
            notes_field.value.strip(),
        )
        for row in add_currency_rows:
            ccy = row["currency"].value
            if not ccy:
                continue
            amt = parse_amount(row["amount"].value)
            add_account_balance(acc_id, ccy, amt)
        refresh_accounts()
        clear_add_form()
        snack("Account added!", SUCCESS)

    add_currency_btn = ft.OutlinedButton(
        "Add Currency",
        icon=ft.Icons.ADD,
        on_click=lambda e: add_currency_row(add_currency_rows, add_currency_column),
    )

    add_btn = ft.ElevatedButton(
        "Create Account",
        icon=ft.Icons.ADD_CIRCLE,
        bgcolor=ACCENT,
        color=ft.Colors.WHITE,
        on_click=add_account_ui,
    )

    # ========== Edit Dialog ==========
    edit_dialog = ft.AlertDialog(modal=True)
    edit_account_id = [None]
    edit_name_field = ft.TextField(label="Account Name", width=240)
    edit_type_field = ft.Dropdown(
        label="Type",
        width=170,
        options=[ft.dropdown.Option(t) for t in ACCOUNT_TYPES],
    )
    edit_notes_field = ft.TextField(label="Notes", width=300)

    edit_currency_rows = []
    edit_currency_column = ft.Column(spacing=10, width=540)

    def open_edit(acc):
        edit_account_id[0] = acc.id
        edit_name_field.value = acc.name
        edit_type_field.value = acc.type
        edit_notes_field.value = acc.notes or ""
        edit_currency_rows.clear()
        edit_currency_column.controls.clear()
        if acc.balances:
            for b in acc.balances:
                add_currency_row(
                    edit_currency_rows,
                    edit_currency_column,
                    initial_currency=b["currency"],
                    initial_amount=f"{b['balance']:.2f}",
                )
        else:
            add_currency_row(edit_currency_rows, edit_currency_column)
        edit_dialog.open = True
        page.dialog = edit_dialog
        page.update()

    def save_edit(e):
        if not edit_name_field.value.strip():
            snack("Name required", WARNING)
            return
        update_account(
            edit_account_id[0],
            name=edit_name_field.value.strip(),
            type=edit_type_field.value or "Cash",
            notes=edit_notes_field.value.strip(),
        )
        for row in edit_currency_rows:
            ccy = row["currency"].value
            if not ccy:
                continue
            amt = parse_amount(row["amount"].value)
            add_account_balance(edit_account_id[0], ccy, amt)
        edit_dialog.open = False
        refresh_accounts()
        snack("Account updated", SUCCESS)
        page.update()

    def cancel_edit(e):
        edit_dialog.open = False
        page.update()

    edit_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("Edit Account", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [edit_name_field, edit_type_field, edit_notes_field], spacing=14
                ),
                ft.Text("Balances", size=13, color=ft.Colors.GREY_600),
                edit_currency_column,
                ft.Row(
                    [
                        ft.OutlinedButton(
                            "Add Currency",
                            icon=ft.Icons.ADD,
                            on_click=lambda e: add_currency_row(
                                edit_currency_rows, edit_currency_column
                            ),
                        ),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Save",
                            on_click=save_edit,
                            bgcolor=ACCENT,
                            color=ft.Colors.WHITE,
                        ),
                        ft.TextButton("Cancel", on_click=cancel_edit),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=10,
                ),
            ],
            spacing=18,
            tight=True,
        ),
        width=850,
        padding=20,
        bgcolor=SURFACE,
        border_radius=16,
    )
    page.overlay.append(edit_dialog)

    # ========== Transfer Dialog (unchanged conceptually, minor styling) ==========
    transfer_dialog = ft.AlertDialog(modal=True)
    transfer_from = ft.Dropdown(label="From", width=250)
    transfer_to = ft.Dropdown(label="To", width=250)
    transfer_ccy = ft.Dropdown(label="Currency", width=140)
    transfer_amt = ft.TextField(label="Amount", width=140, keyboard_type="number")

    def open_transfer(e=None):
        accts = get_accounts()
        transfer_from.options = [ft.dropdown.Option(str(a.id), a.name) for a in accts]
        transfer_to.options = [ft.dropdown.Option(str(a.id), a.name) for a in accts]
        transfer_ccy.options = [ft.dropdown.Option(c) for c in ALL_CURRENCIES]
        transfer_from.value = None
        transfer_to.value = None
        transfer_ccy.value = None
        transfer_amt.value = ""
        transfer_dialog.open = True
        page.dialog = transfer_dialog
        page.update()

    def do_transfer(e):
        if not (
            transfer_from.value
            and transfer_to.value
            and transfer_ccy.value
            and transfer_amt.value
        ):
            snack("All fields required", WARNING)
            return
        if transfer_from.value == transfer_to.value:
            snack("Choose different accounts", WARNING)
            return
        amt = parse_amount(transfer_amt.value)
        if amt <= 0:
            snack("Amount must be > 0", WARNING)
            return
        add_account_balance(int(transfer_from.value), transfer_ccy.value, -amt)
        add_account_balance(int(transfer_to.value), transfer_ccy.value, amt)
        transfer_dialog.open = False
        refresh_accounts()
        snack("Transfer complete", SUCCESS)
        page.update()

    transfer_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("Transfer Money", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([transfer_from, transfer_to], spacing=14),
                ft.Row([transfer_ccy, transfer_amt], spacing=14),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Transfer",
                            on_click=do_transfer,
                            bgcolor=SUCCESS,
                            color=ft.Colors.WHITE,
                        ),
                        ft.TextButton("Cancel", on_click=lambda e: close_transfer()),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=10,
                ),
            ],
            spacing=16,
        ),
        width=640,
        padding=20,
        bgcolor=SURFACE,
        border_radius=16,
    )
    page.overlay.append(transfer_dialog)

    def close_transfer():
        transfer_dialog.open = False
        page.update()

    # ========== Accounts List ==========
    accounts_column = ft.Column(spacing=16, width=900)

    def build_card(acc):
        balances = (
            ", ".join(f"{b['currency']}: {b['balance']:.2f}" for b in acc.balances)
            or "No balances"
        )
        return ft.Container(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(acc.name, size=18, weight=ft.FontWeight.W_600),
                            ft.Text(
                                f"Type: {acc.type}", size=12, color=ft.Colors.GREY_600
                            ),
                            ft.Text(
                                f"Balances: {balances}",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Text(
                                f"Notes: {acc.notes or '-'}",
                                size=11,
                                color=ft.Colors.GREY_600,
                                italic=True,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.SWAP_HORIZ,
                                tooltip="Transfer",
                                on_click=open_transfer,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREY_100,
                                    color=SUCCESS,
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip="Edit",
                                on_click=lambda e, a=acc: open_edit(a),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREY_100,
                                    color=ACCENT,
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_ROUNDED,
                                tooltip="Delete",
                                on_click=lambda e, acc_id=acc.id: delete_account_ui(
                                    acc_id
                                ),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREY_100,
                                    color=DANGER,
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                            ),
                        ],
                        spacing=6,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            bgcolor=SURFACE,
            border_radius=18,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=16,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 6),
            ),
        )

    def refresh_accounts():
        accounts_column.controls.clear()
        data = get_accounts()
        if not data:
            accounts_column.controls.append(
                ft.Container(
                    ft.Text(
                        "No accounts yet. Create one above.", color=ft.Colors.GREY_600
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for acc in data:
                accounts_column.controls.append(build_card(acc))
        if accounts_column.page:
            accounts_column.update()

    def delete_account_ui(acc_id):
        delete_account(acc_id)
        refresh_accounts()
        snack("Account deleted", DANGER)

    # ========== Snack helper ==========
    def snack(msg, color):
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        if page:
            page.update()

    # Initial load
    refresh_accounts()

    # ========== Layout ==========
    add_section = ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Add Account", size=24, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.OutlinedButton(
                            "Transfer Money",
                            icon=ft.Icons.SWAP_HORIZ,
                            on_click=open_transfer,
                            style=ft.ButtonStyle(
                                side=ft.BorderSide(1, SUCCESS),
                                color=SUCCESS,
                                shape=ft.RoundedRectangleBorder(radius=12),
                            ),
                        ),
                    ]
                ),
                ft.Divider(
                    height=20, color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK)
                ),
                ft.ResponsiveRow(
                    [
                        ft.Container(name_field, col={"xs": 12, "md": 4}),
                        ft.Container(type_field, col={"xs": 6, "md": 3}),
                        ft.Container(notes_field, col={"xs": 12, "md": 5}),
                    ],
                    run_spacing=10,
                ),
                ft.Text("Balances", size=13, color=ft.Colors.GREY_600),
                add_currency_column,
                ft.Row(
                    [
                        add_currency_btn,
                        ft.Container(expand=True),
                        add_btn,
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=18,
        ),
        width=900,
        padding=28,
        bgcolor=SURFACE,
        border_radius=26,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 8),
        ),
        margin=ft.margin.only(top=30, bottom=10),
    )

    accounts_section = ft.Container(
        ft.Column(
            [
                ft.Text("Accounts", size=22, weight=ft.FontWeight.W_600),
                accounts_column,
            ],
            spacing=20,
        ),
        width=900,
        padding=ft.padding.only(top=10, bottom=40),
    )

    root = ft.Container(
        content=ft.Column(
            [
                add_section,
                ft.Divider(
                    height=1, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK)
                ),
                accounts_section,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll="auto",
            spacing=6,
        ),
        expand=True,
        alignment=ft.alignment.top_center,
        bgcolor=BG,
    )

    return root
