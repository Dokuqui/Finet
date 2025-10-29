import csv
import datetime
import os
import flet as ft
import traceback

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
    get_category_id_by_name,
    update_category,
)
from app.db.recurring import (
    create_recurring,
    generate_due_transactions,
)
from app.ui.util import (
    EXAMPLE_CSV_EXPLANATIONS,
    EXAMPLE_CSV_FULL,
)

# --- FIX: Moved this import to the top ---
from app.services.converter import get_active_currency_codes
# --- END FIX ---

ERROR_COLOR = ft.Colors.RED_400

# ----------------- Icon Catalog -----------------
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


def get_icon_by_name(name: str):
    return next(
        (ic["icon"] for ic in ICON_CHOICES if ic["name"] == name), ft.Icons.CATEGORY
    )


# ----------------- Design Tokens -----------------
class UX:
    BG = ft.Colors.GREY_50
    SURFACE = ft.Colors.WHITE
    SURFACE_ALT = ft.Colors.GREY_100
    BORDER = ft.Colors.GREY_300
    TEXT = ft.Colors.GREY_900
    MUTED = ft.Colors.GREY_600
    ACCENT = ft.Colors.BLUE_400
    ACCENT_ALT = ft.Colors.BLUE_600
    POSITIVE = ft.Colors.GREEN_400
    NEGATIVE = ft.Colors.RED_400
    WARN = ft.Colors.AMBER_400

    R_SM = 8
    R_MD = 14
    R_LG = 20
    R_XL = 26

    SHADOW_SOFT = ft.BoxShadow(
        spread_radius=1,
        blur_radius=18,
        color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
        offset=ft.Offset(0, 6),
    )
    SHADOW_CARD = ft.BoxShadow(
        spread_radius=1,
        blur_radius=12,
        color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
        offset=ft.Offset(0, 4),
    )


def _handle_file_picker_result(
    e: ft.FilePickerResultEvent, page: ft.Page, notify_func, export_func, import_func
):
    """
    Handles results from both pick_files and save_file.
    Requires page and notify function to be passed in.
    """
    print("[FilePicker] on_result triggered!")

    if e.path:
        print("[FilePicker] Detected save operation, calling export_func...")
        export_func(e.path, page, notify_func)
    elif e.files and len(e.files) > 0 and e.files[0].path:
        print("[FilePicker] Detected pick operation, calling import_func...")
        import_func(e.files[0].path, page, notify_func)
    else:
        print("[FilePicker] Operation cancelled.")
        notify_func("Operation cancelled.", UX.MUTED)


def export_to_csv(path, page, notify):
    print(f"[Export CSV] Function called with path: {path}")
    if not path:
        notify("Export cancelled or no path selected.", UX.MUTED)
        return
    print(f"[Export CSV] Attempting to save to: {path}")
    try:
        txs = get_recent_transactions(limit=10000)
        print(f"[Export CSV] Fetched {len(txs)} transactions.")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["date", "amount", "category", "account_id", "notes", "currency"]
            )
            for tx in txs:
                writer.writerow(
                    [
                        tx.date,
                        tx.amount,
                        tx.category_name or "N/A",
                        tx.account_id if tx.account_id is not None else "N/A",
                        tx.notes or "",
                        tx.currency,
                    ]
                )
        print(f"[Export CSV] Successfully wrote {len(txs)} rows to {path}")
        notify(
            f"Exported {len(txs)} transactions to {os.path.basename(path)}", UX.POSITIVE
        )
    except Exception as ex:
        print("-" * 20)
        print("[Export CSV] Error occurred:")
        print(f"   Path: {path}")
        print(f"   Error Type: {type(ex).__name__}")
        print(f"   Error Details: {ex}")
        traceback.print_exc()
        print("-" * 20)
        notify(
            f"Export Error: {type(ex).__name__} - Check console.",
            ERROR_COLOR,
            duration=5000,
        )


def import_from_csv(path, page, notify):
    print(f"[Import CSV] Function called with path: {path}")
    if not path:
        notify("No file selected", UX.MUTED)
        return
    try:
        imported, skipped = 0, 0
        all_categories = get_categories()
        cat_map_by_name = {c["name"].lower(): c for c in all_categories}
        other_cat_id = get_category_id_by_name("Other")
        if other_cat_id is None:
            print(
                "[Import CSV] Warning: 'Other' category not found. Skipped rows might increase."
            )

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            processed_rows = []
            for row in reader:
                processed_rows.append(row)

        print(f"[Import CSV] Read {len(processed_rows)} rows from file.")

        for row in processed_rows:
            cat_name = row.get("category", "").strip().lower()
            category = cat_map_by_name.get(cat_name)
            cat_id = category["id"] if category else other_cat_id

            if not category and other_cat_id is None:
                print(
                    f"[Import CSV] Skipping row due to missing category '{cat_name}' and no 'Other' fallback. Row: {row}"
                )
                skipped += 1
                continue
            elif not category:
                skipped += 1

            try:
                amt = float(row["amount"])
                acc_id_str = row.get("account_id") or row.get("account")
                if not acc_id_str:
                    raise ValueError("Missing account_id/account column")
                acc_id = int(acc_id_str.strip())
                currency = row.get("currency", "").strip().upper()
                if not currency:
                    raise ValueError("Missing currency column")
                date_str = row.get("date", "").strip()
                if not date_str:
                    raise ValueError("Missing date column")
                datetime.date.fromisoformat(date_str)

                add_transaction(
                    date_str,
                    amt,
                    cat_id,
                    acc_id,
                    row.get("notes", "").strip(),
                    currency,
                )
                increment_account_balance(acc_id, currency, amt)
                imported += 1
            except Exception as row_ex:
                print(f"[Import CSV] Skipping row due to error: {row_ex} | Row: {row}")
                skipped += 1

        print(f"[Import CSV] Processed: {imported} imported, {skipped} skipped.")
        notify(f"Import complete: {imported} added, {skipped} skipped.", UX.ACCENT)

    except FileNotFoundError:
        print(f"[Import CSV] Error: File not found at {path}")
        notify("Import Error: File not found.", ERROR_COLOR, duration=5000)
    except Exception as ex:
        print(f"[Import CSV] Error: {ex}")
        traceback.print_exc()
        notify(
            f"Import Error: {type(ex).__name__} - Check console/logs.",
            ERROR_COLOR,
            duration=5000,
        )


# ----------------- Main Page -----------------
def transactions_page(page: ft.Page, file_picker: ft.FilePicker):
    page.bgcolor = UX.BG
    page.padding = 0
    print("[TransactionsPage] Rebuilding page content...")  # Helpful for debugging

    # ---------- Snackbar helper ----------
    def notify(msg: str, color=UX.ACCENT, duration=3000):
        if not page:
            return
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color, duration=duration)
        page.snack_bar.open = True
        page.update()

    # ---------- Category Data ----------
    def fetch_categories():
        return get_categories()

    def build_category_dropdown_options():
        return [ft.dropdown.Option(str(c["id"]), c["name"]) for c in fetch_categories()]

    # ---------- Fields & State ----------
    selected_date_display = ft.Text("", size=12, color=UX.MUTED)
    amount_field = ft.TextField(
        label="Amount",
        value="0.00",
        keyboard_type="number",
        width=180,
        border_radius=UX.R_MD,
    )
    notes_field = ft.TextField(
        label="Notes",
        multiline=False,
        width=420,
        border_radius=UX.R_MD,
    )

    accounts = get_accounts()
    account_field = ft.Dropdown(
        label="Account",
        width=260,
        options=[
            ft.dropdown.Option(str(a.id), f"{a.name} ({a.type})") for a in accounts
        ],
        border_radius=UX.R_MD,
    )
    currency_field = ft.Dropdown(
        label="Currency",
        width=130,
        options=[],
        border_radius=UX.R_MD,
    )
    category_field = ft.Dropdown(
        label="Category",
        width=220,
        options=build_category_dropdown_options(),
        border_radius=UX.R_MD,
    )

    selected_date_value = [datetime.date.today().isoformat()]

    # ---------- Date Picker ----------
    def on_date_change(e: ft.ControlEvent):
        try:
            d = e.data
            if isinstance(d, str):
                selected_date_value[0] = d[:10]
            else:
                selected_date_value[0] = datetime.date.today().isoformat()
        except Exception:
            selected_date_value[0] = datetime.date.today().isoformat()
        selected_date_display.value = selected_date_value[0]
        page.update()

    def on_date_dismiss(e):
        notify("Date selection dismissed.", UX.MUTED)

    date_picker = ft.DatePicker(
        first_date=datetime.date(2024, 1, 1),
        last_date=datetime.date(2036, 12, 31),
        on_change=on_date_change,
        on_dismiss=on_date_dismiss,
    )
    page.overlay.append(date_picker)

    date_btn = ft.ElevatedButton(
        "Choose Date",
        icon=ft.Icons.CALENDAR_MONTH,
        on_click=lambda e: page.open(date_picker),
        bgcolor=UX.SURFACE_ALT,
        color=UX.ACCENT,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=UX.R_MD)),
        height=40,
    )

    # ---------- Amount Stepper ----------
    def adjust_amount(delta: float):
        try:
            val = float(amount_field.value)
        except ValueError:
            val = 0.0
        val = max(val + delta, 0)
        amount_field.value = f"{val:.2f}"
        page.update()

    stepper = ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.REMOVE,
                tooltip="-1",
                on_click=lambda e: adjust_amount(-1),
                style=ft.ButtonStyle(
                    bgcolor=UX.SURFACE_ALT,
                    color=UX.ACCENT,
                    shape=ft.RoundedRectangleBorder(radius=UX.R_SM),
                ),
                width=40,
                height=40,
            ),
            amount_field,
            ft.IconButton(
                icon=ft.Icons.ADD,
                tooltip="+1",
                on_click=lambda e: adjust_amount(1),
                style=ft.ButtonStyle(
                    bgcolor=UX.SURFACE_ALT,
                    color=UX.ACCENT,
                    shape=ft.RoundedRectangleBorder(radius=UX.R_SM),
                ),
                width=40,
                height=40,
            ),
        ],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ---------- Account -> Currency dynamic ----------
    def on_account_change(e):
        val = account_field.value
        currency_field.options = []
        currency_field.value = None

        if not val:
            page.update()
            return

        acc = next((a for a in accounts if str(a.id) == val), None)
        if acc and acc.balances:
            currency_field.options = [
                ft.dropdown.Option(b["currency"]) for b in acc.balances
            ]
            currency_field.value = acc.balances[0]["currency"]
        elif acc and not acc.balances:
            # --- THIS IS THE FIX ---
            # This logic is correct. We just moved the import to the top.
            try:
                active_codes = get_active_currency_codes()
                currency_field.options = [ft.dropdown.Option(c) for c in active_codes]
            except Exception as ex:
                print(f"Warning: Could not import get_active_currency_codes: {ex}")
                currency_field.options = [
                    ft.dropdown.Option("EUR"),
                    ft.dropdown.Option("USD"),
                ]
            # --- END FIX ---
        page.update()

    account_field.on_change = on_account_change

    # ---------- Category Management Dialogs ----------
    add_dialog = ft.AlertDialog(modal=True)
    edit_dialog = ft.AlertDialog(modal=True)
    list_dialog = ft.AlertDialog(modal=True)

    add_category_name = ft.TextField(label="Name", width=230)
    add_category_icon = ft.Dropdown(
        label="Icon",
        options=[ft.dropdown.Option(ic["name"]) for ic in ICON_CHOICES],
        value="Other",
        width=170,
    )
    add_category_type = ft.Dropdown(
        label="Type",
        options=[
            ft.dropdown.Option("expense", "Expense (Money out)"),
            ft.dropdown.Option("income", "Income (Money in)"),
        ],
        value="expense",
        width=230,
    )
    add_icon_preview = ft.Icon(get_icon_by_name("Other"), size=34)
    add_feedback = ft.Text("", color=UX.NEGATIVE, size=12)

    def on_add_icon_change(e):
        add_icon_preview.name = get_icon_by_name(add_category_icon.value)
        page.update()

    add_category_icon.on_change = on_add_icon_change

    def open_add_category(e=None):
        add_category_name.value = ""
        add_category_icon.value = "Other"
        add_category_type.value = "expense"
        add_icon_preview.name = get_icon_by_name("Other")
        add_feedback.value = ""
        add_dialog.open = True
        page.dialog = add_dialog
        page.update()

    def close_add_category(e=None):
        add_dialog.open = False
        page.update()

    def save_new_category(e):
        name = add_category_name.value.strip()
        if not name:
            add_feedback.value = "Name is required."
            page.update()
            return
        try:
            cat_type = add_category_type.value or "expense"
            add_category(name, add_category_icon.value, cat_type)
            close_add_category()
            refresh_categories_main()
            notify("Category added", UX.POSITIVE)
        except Exception as ex:
            add_feedback.value = f"Error: {ex}"
            page.update()

    add_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("New Category", size=20, weight=ft.FontWeight.W_600),
                ft.Row(
                    [add_category_name, ft.Container(width=10), add_category_icon],
                    spacing=0,
                ),
                add_category_type,
                ft.Row(
                    [
                        ft.Container(
                            add_icon_preview,
                            padding=ft.padding.all(10),
                            bgcolor=UX.SURFACE_ALT,
                            border_radius=UX.R_MD,
                        ),
                        ft.Container(expand=True),
                    ]
                ),
                add_feedback,
                ft.Row(
                    [
                        ft.TextButton("Cancel", on_click=close_add_category),
                        ft.ElevatedButton(
                            "Save",
                            icon=ft.Icons.SAVE,
                            bgcolor=UX.ACCENT,
                            color=ft.Colors.WHITE,
                            on_click=save_new_category,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=16,
        ),
        width=520,
        padding=24,
        bgcolor=UX.SURFACE,
        border_radius=UX.R_LG,
        shadow=UX.SHADOW_CARD,
    )
    page.overlay.append(add_dialog)

    # Edit dialog
    edit_category_id = [None]
    edit_category_name = ft.TextField(label="Name", width=230)
    edit_category_icon = ft.Dropdown(
        label="Icon",
        options=[ft.dropdown.Option(ic["name"]) for ic in ICON_CHOICES],
        value="Other",
        width=170,
    )
    edit_category_type = ft.Dropdown(
        label="Type",
        options=[
            ft.dropdown.Option("expense", "Expense (Money out)"),
            ft.dropdown.Option("income", "Income (Money in)"),
        ],
        value="expense",
        width=230,
    )
    edit_icon_preview = ft.Icon(get_icon_by_name("Other"), size=34)
    edit_feedback = ft.Text("", color=UX.NEGATIVE, size=12)

    def on_edit_icon_change(e):
        edit_icon_preview.name = get_icon_by_name(edit_category_icon.value)
        page.update()

    edit_category_icon.on_change = on_edit_icon_change

    def open_edit_category(cat):
        edit_category_id[0] = cat["id"]
        edit_category_name.value = cat["name"]
        icon_val = cat.get("icon") or "Other"
        edit_category_icon.value = icon_val
        edit_category_type.value = cat.get("type") or "expense"
        edit_icon_preview.name = get_icon_by_name(icon_val)
        edit_feedback.value = ""
        edit_dialog.open = True
        page.dialog = edit_dialog
        page.update()

    def close_edit_category(e=None):
        edit_dialog.open = False
        page.update()

    def save_edit_category(e):
        name = edit_category_name.value.strip()
        if not name:
            edit_feedback.value = "Name is required."
            page.update()
            return
        try:
            cat_type = edit_category_type.value or "expense"
            update_category(
                edit_category_id[0], name, edit_category_icon.value, cat_type
            )
            close_edit_category()
            refresh_categories_main()
            refresh_category_list()
            notify("Category updated", UX.POSITIVE)
        except Exception as ex:
            edit_feedback.value = f"Error: {ex}"
            page.update()

    edit_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("Edit Category", size=20, weight=ft.FontWeight.W_600),
                ft.Row(
                    [edit_category_name, ft.Container(width=10), edit_category_icon],
                    spacing=0,
                ),
                edit_category_type,
                ft.Row(
                    [
                        ft.Container(
                            edit_icon_preview,
                            padding=ft.padding.all(10),
                            bgcolor=UX.SURFACE_ALT,
                            border_radius=UX.R_MD,
                        ),
                        ft.Container(expand=True),
                    ]
                ),
                edit_feedback,
                ft.Row(
                    [
                        ft.TextButton("Cancel", on_click=close_edit_category),
                        ft.ElevatedButton(
                            "Save",
                            icon=ft.Icons.SAVE,
                            bgcolor=UX.ACCENT,
                            color=ft.Colors.WHITE,
                            on_click=save_edit_category,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=16,
        ),
        width=520,
        padding=24,
        bgcolor=UX.SURFACE,
        border_radius=UX.R_LG,
        shadow=UX.SHADOW_CARD,
    )
    page.overlay.append(edit_dialog)

    categories_grid = ft.Column(spacing=10, scroll="auto")

    list_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Categories", size=20, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            tooltip="Add",
                            on_click=open_add_category,
                            style=ft.ButtonStyle(
                                bgcolor=UX.SURFACE_ALT,
                                color=UX.ACCENT,
                                shape=ft.RoundedRectangleBorder(radius=UX.R_SM),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=10),
                categories_grid,
                ft.Container(height=4),
                ft.Row(
                    [
                        ft.TextButton("Close", on_click=lambda e: close_list_dialog()),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=14,
        ),
        width=560,
        height=520,
        padding=24,
        bgcolor=UX.SURFACE,
        border_radius=UX.R_LG,
        shadow=UX.SHADOW_CARD,
    )
    page.overlay.append(list_dialog)

    def open_list_dialog(e=None):
        refresh_category_list()
        list_dialog.open = True
        page.dialog = list_dialog
        page.update()

    def close_list_dialog(e=None):
        list_dialog.open = False
        page.update()

    def delete_category_ui(cat_id):
        delete_category(cat_id)
        refresh_categories_main()
        refresh_category_list()
        notify("Category deleted", UX.NEGATIVE)

    def refresh_category_list():
        categories_grid.controls.clear()
        cats = fetch_categories()
        if not cats:
            categories_grid.controls.append(
                ft.Text("No categories yet.", color=UX.MUTED)
            )
        else:
            rows = []
            for cat in cats:
                icon_name = cat.get("icon") or "Other"
                cat_type = cat.get("type", "expense")
                type_color = UX.POSITIVE if cat_type == "income" else UX.NEGATIVE
                chip = ft.Container(
                    ft.Row(
                        [
                            ft.Icon(
                                get_icon_by_name(icon_name), size=20, color=UX.ACCENT
                            ),
                            ft.Text(cat["name"], size=13, weight=ft.FontWeight.W_500),
                            ft.Text(
                                cat_type.upper(),
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=type_color,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip="Edit",
                                on_click=lambda e, c=cat: open_edit_category(c),
                                style=ft.ButtonStyle(
                                    bgcolor=UX.SURFACE_ALT,
                                    color=UX.ACCENT,
                                    shape=ft.RoundedRectangleBorder(radius=UX.R_SM),
                                ),
                                icon_size=16,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Delete",
                                on_click=lambda e, cid=cat["id"]: delete_category_ui(
                                    cid
                                ),
                                style=ft.ButtonStyle(
                                    bgcolor=UX.SURFACE_ALT,
                                    color=UX.NEGATIVE,
                                    shape=ft.RoundedRectangleBorder(radius=UX.R_SM),
                                ),
                                icon_size=16,
                            ),
                        ],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLUE_50),
                    border_radius=UX.R_LG,
                )
                rows.append(chip)
            categories_grid.controls.extend(rows)
        if categories_grid.page:
            categories_grid.update()

    def refresh_categories_main():
        category_field.options = build_category_dropdown_options()
        if category_field.page:
            category_field.update()

    # ---------- Recurring Controls ----------
    recurring_switch = ft.Switch(label="Recurring or Planned", value=False)
    frequency_field = ft.Dropdown(
        label="Frequency",
        options=[
            ft.dropdown.Option("once", "One-Time (Planned)"),
            ft.dropdown.Option("daily"),
            ft.dropdown.Option("weekly"),
            ft.dropdown.Option("monthly"),
            ft.dropdown.Option("yearly"),
            ft.dropdown.Option("custom_interval"),
        ],
        width=180,
        visible=False,
    )
    interval_field = ft.TextField(
        label="Interval",
        width=110,
        visible=False,
        tooltip="Only for custom_interval: number of days",
    )
    day_of_month_field = ft.TextField(
        label="Day of Month",
        width=130,
        visible=False,
        tooltip="Only for monthly: 1-31 (optional; blank = use start date day)",
    )
    end_date_field = ft.TextField(
        label="End Date (YYYY-MM-DD)",
        width=180,
        visible=False,
        tooltip="Optional final date",
    )

    def _toggle_recurring(e):
        show = recurring_switch.value
        frequency_field.visible = show

        freq = frequency_field.value
        end_date_field.visible = show and (freq != "once")
        interval_field.visible = show and (freq == "custom_interval")
        day_of_month_field.visible = show and (freq == "monthly")
        page.update()

    def _freq_changed(e):
        freq = frequency_field.value
        interval_field.visible = freq == "custom_interval"
        day_of_month_field.visible = freq == "monthly"
        end_date_field.visible = freq != "once"
        page.update()

    recurring_switch.on_change = _toggle_recurring
    frequency_field.on_change = _freq_changed

    recurring_controls_row = ft.Row(
        [
            recurring_switch,
            frequency_field,
            interval_field,
            day_of_month_field,
            end_date_field,
        ],
        spacing=12,
        wrap=True,
    )

    # ---------- Transactions List ----------
    transaction_list = ft.Column(spacing=18)

    def transaction_color(tx_amount: float):
        return UX.POSITIVE if tx_amount > 0 else UX.NEGATIVE

    def build_transaction_card(tx):
        category_name = tx.category_name or "Other"
        icon_name = getattr(tx, "category_icon", "Other")
        color = transaction_color(tx.amount)
        date_str = str(tx.date)[:10]
        amount_text = f"{tx.currency} {abs(tx.amount):.2f}"

        badge = (
            ft.Container(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.REPEAT, size=14, color=UX.ACCENT),
                        ft.Text("Recurring", size=10, color=UX.ACCENT),
                    ],
                    spacing=4,
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                bgcolor=ft.Colors.with_opacity(0.15, UX.ACCENT),
                border_radius=UX.R_SM,
                margin=ft.margin.only(bottom=4),
            )
            if tx.recurring_id
            else None
        )

        left_meta_col = [
            ft.Text(category_name, size=15, weight=ft.FontWeight.W_600),
            ft.Row(
                [
                    ft.Text(date_str, size=11, color=UX.MUTED),
                    ft.Text(f"Acct: {tx.account_id}", size=11, color=UX.MUTED),
                    ft.Text(tx.currency, size=11, color=UX.MUTED),
                ],
                spacing=10,
            ),
            ft.Text(
                tx.notes or "",
                size=11,
                color=UX.MUTED,
                italic=True,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ]
        if badge:
            left_meta_col.insert(0, badge)

        return ft.Container(
            ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                ft.Icon(
                                    get_icon_by_name(icon_name), color=color, size=26
                                ),
                                padding=ft.padding.all(10),
                                bgcolor=ft.Colors.with_opacity(0.25, color),
                                border_radius=UX.R_MD,
                            ),
                            ft.Column(left_meta_col, spacing=3),
                        ],
                        spacing=14,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                amount_text,
                                size=16,
                                weight=ft.FontWeight.W_700,
                                color=color,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_ROUNDED,
                                tooltip="Delete",
                                on_click=lambda e, tid=tx.id: delete_tx(tid),
                                style=ft.ButtonStyle(
                                    bgcolor=UX.SURFACE_ALT,
                                    color=UX.NEGATIVE,
                                    shape=ft.RoundedRectangleBorder(radius=UX.R_SM),
                                ),
                                icon_size=20,
                                width=40,
                                height=40,
                            ),
                        ],
                        spacing=4,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.all(16),
            bgcolor=UX.SURFACE,
            border_radius=UX.R_LG,
            shadow=UX.SHADOW_CARD,
            border=ft.border.only(left=ft.BorderSide(5, color)),
        )

    def refresh_transactions():
        txs = get_recent_transactions()
        transaction_list.controls.clear()
        if not txs:
            transaction_list.controls.append(
                ft.Container(
                    ft.Text("No transactions yet.", color=UX.MUTED, size=13),
                    padding=ft.padding.all(28),
                    bgcolor=UX.SURFACE,
                    border_radius=UX.R_LG,
                )
            )
        else:
            for tx in txs:
                transaction_list.controls.append(build_transaction_card(tx))
        if transaction_list.page:
            transaction_list.update()

    # ------------------ Refresh Function ------------------
    def refresh_page_data():
        nonlocal accounts
        accounts = get_accounts()

        account_field.options = [
            ft.dropdown.Option(str(a.id), f"{a.name} ({a.type})") for a in accounts
        ]

        on_account_change(None)

        if page:
            page.update()

    # ---------- Add Transaction Logic ----------
    def reset_form():
        amount_field.value = "0.00"
        notes_field.value = ""
        category_field.value = None
        account_field.value = None
        currency_field.value = None
        recurring_switch.value = False
        frequency_field.value = None
        frequency_field.visible = False
        interval_field.value = ""
        interval_field.visible = False
        day_of_month_field.value = ""
        day_of_month_field.visible = False
        end_date_field.value = ""
        end_date_field.visible = False
        selected_date_value[0] = datetime.date.today().isoformat()
        selected_date_display.value = selected_date_value[0]

    def add_tx(e):
        if not category_field.value:
            notify("Select a category", UX.WARN)
            return
        if not account_field.value:
            notify("Select an account", UX.WARN)
            return
        if not currency_field.value:
            notify("Select currency", UX.WARN)
            return
        try:
            raw_amt = float(amount_field.value)
        except ValueError:
            notify("Invalid amount", UX.NEGATIVE)
            return

        date_iso = selected_date_value[0]
        category_id = int(category_field.value)
        account_id = int(account_field.value)
        currency = currency_field.value

        cats_now = fetch_categories()
        category_obj = next((c for c in cats_now if c["id"] == category_id), None)

        if not category_obj:
            notify("Category not found. Please refresh.", UX.NEGATIVE)
            return

        is_income = category_obj.get("type") == "income"
        signed_amount = raw_amt if is_income else -abs(raw_amt)

        if recurring_switch.value:
            freq = frequency_field.value
            if not freq:
                notify("Select frequency", UX.WARN)
                return

            interval = None
            if freq == "custom_interval":
                if not interval_field.value.strip():
                    notify("Interval required for custom interval", UX.WARN)
                    return
                try:
                    interval = int(interval_field.value)
                    if interval <= 0:
                        raise ValueError
                except ValueError:
                    notify("Interval must be a positive integer", UX.NEGATIVE)
                    return

            day_of_month = None
            if freq == "monthly" and day_of_month_field.value.strip():
                try:
                    day_of_month = int(day_of_month_field.value)
                    if day_of_month < 1 or day_of_month > 31:
                        raise ValueError
                except ValueError:
                    notify("Day of month must be 1..31", UX.NEGATIVE)
                    return

            end_date = end_date_field.value.strip() or None

            create_recurring(
                account_id=account_id,
                category_id=category_id,
                amount=signed_amount,
                currency=currency,
                frequency=freq,
                start_date=date_iso,
                end_date=end_date,
                notes=notes_field.value.strip(),
                interval=interval,
                day_of_month=day_of_month,
            )

            newly = generate_due_transactions()
            refresh_transactions()
            reset_form()
            page.update()
            notify(
                f"Recurring pattern created (generated {newly} occurrence{'s' if newly != 1 else ''})",
                UX.POSITIVE,
            )
            return

        add_transaction(
            date_iso,
            signed_amount,
            category_id,
            account_id,
            notes_field.value.strip(),
            currency,
        )
        increment_account_balance(account_id, currency, signed_amount)

        refresh_transactions()
        reset_form()
        page.update()
        notify("Transaction added", UX.POSITIVE)

    def delete_tx(txid: int):
        delete_transaction(txid)
        refresh_transactions()
        notify("Transaction deleted", UX.NEGATIVE)

    add_tx_btn = ft.ElevatedButton(
        "Add Transaction",
        icon=ft.Icons.ADD_CIRCLE,
        bgcolor=UX.ACCENT,
        color=ft.Colors.WHITE,
        on_click=add_tx,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UX.R_MD),
            elevation=4,
        ),
        height=46,
    )

    # --- CSV Example Dialog ---
    example_csv_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Import CSV Format Example"),
        content=ft.Column(
            [
                ft.Text(
                    "Use this format for your CSV file. The header row is required.",
                    size=13,
                ),
                ft.TextField(
                    value=EXAMPLE_CSV_FULL,
                    multiline=True,
                    read_only=True,
                    border_color=UX.BORDER,
                    height=150,  # Adjust height as needed
                    text_size=12,
                ),
                ft.ElevatedButton(
                    "Copy Example Data to Clipboard",
                    icon=ft.Icons.COPY,
                    on_click=lambda _: (
                        page.set_clipboard(EXAMPLE_CSV_FULL),
                        notify("Example CSV copied!", UX.POSITIVE),
                    ),
                ),
                ft.Divider(height=10),
                ft.Markdown(  # Use Markdown for explanations
                    EXAMPLE_CSV_EXPLANATIONS,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.COMMON_MARK,
                ),
            ],
            tight=True,  # Make column fit content vertically
            scroll="auto",  # Allow scrolling if content overflows vertically
            width=600,  # Set a reasonable width
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda _: close_example_dialog()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_example_dialog(e=None):
        if (
            example_csv_dialog not in page.overlay
        ):  # Ensure dialog is added if not already
            page.overlay.append(example_csv_dialog)
        page.dialog = example_csv_dialog
        example_csv_dialog.open = True
        page.update()

    def close_example_dialog(e=None):
        example_csv_dialog.open = False
        page.update()

    # ---------- Import / Export ----------
    import_button = ft.ElevatedButton(
        "Import CSV",
        icon=ft.Icons.FILE_UPLOAD,
        bgcolor=UX.SURFACE_ALT,
        color=UX.ACCENT,
        on_click=lambda _: file_picker.pick_files(
            dialog_title="Select CSV to Import",
            allow_multiple=False,
            allowed_extensions=["csv"],
        ),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=UX.R_MD)),
        height=40,
    )

    export_button = ft.ElevatedButton(
        "Export CSV",
        icon=ft.Icons.FILE_DOWNLOAD,
        bgcolor=UX.SURFACE_ALT,
        color=UX.ACCENT,
        on_click=lambda _: file_picker.save_file(
            dialog_title="Save Transactions CSV",
            file_name="transactions.csv",
            allowed_extensions=["csv"],
        ),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=UX.R_MD)),
        height=40,
    )

    show_example_button = ft.TextButton(
        "Show CSV Example",
        icon=ft.Icons.INFO_OUTLINE,
        tooltip="View the required CSV format for importing",
        on_click=open_example_dialog,
        # style=ft.ButtonStyle(color=UX.MUTED), # Optional styling
    )

    # ---------- Utility Panel ----------
    util_panel = ft.Container(
        ft.Column(
            [
                ft.Text("Utilities", size=18, weight=ft.FontWeight.W_600),
                ft.Divider(
                    height=16, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)
                ),
                ft.ElevatedButton(
                    "Categories",
                    icon=ft.Icons.LIST,
                    on_click=open_list_dialog,
                    bgcolor=UX.SURFACE_ALT,
                    color=UX.ACCENT,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=UX.R_MD),
                    ),
                    height=40,
                ),
                ft.ElevatedButton(
                    "Add Category",
                    icon=ft.Icons.ADD,
                    on_click=open_add_category,
                    bgcolor=UX.ACCENT,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=UX.R_MD),
                    ),
                    height=40,
                ),
                ft.Divider(
                    height=24, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
                ),
                import_button,
                export_button,
                show_example_button,
            ],
            spacing=16,
            alignment=ft.MainAxisAlignment.START,
        ),
        width=200,
        padding=ft.padding.all(22),
        bgcolor=UX.SURFACE,
        border_radius=UX.R_LG,
        shadow=UX.SHADOW_SOFT,
        margin=ft.margin.only(top=40, left=10, right=10, bottom=40),
    )

    # ---------- Add Transaction Card ----------
    add_card = ft.Container(
        ft.Column(
            [
                ft.Text("Add Transaction", size=24, weight=ft.FontWeight.W_600),
                ft.Divider(
                    height=20, color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK)
                ),
                ft.Row(
                    [date_btn, selected_date_display],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                stepper,
                ft.Row([category_field, account_field, currency_field], spacing=16),
                notes_field,
                recurring_controls_row,
                ft.Container(
                    add_tx_btn,
                    alignment=ft.alignment.center_left,
                    margin=ft.margin.only(top=12),
                ),
            ],
            spacing=18,
        ),
        width=760,
        padding=ft.padding.all(34),
        bgcolor=UX.SURFACE,
        border_radius=UX.R_XL,
        shadow=UX.SHADOW_SOFT,
        margin=ft.margin.only(top=38, bottom=12),
    )

    # ---------- Transactions Section ----------
    transactions_section = ft.Container(
        ft.Column(
            [
                ft.Text("Recent Transactions", size=21, weight=ft.FontWeight.W_600),
                transaction_list,
            ],
            spacing=20,
        ),
        width=760,
        padding=ft.padding.only(bottom=40),
    )

    refresh_transactions()
    refresh_category_list()
    selected_date_display.value = selected_date_value[0]

    # ---------- Root Layout ----------
    root = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    ft.Column(
                        [
                            add_card,
                            transactions_section,
                        ],
                        spacing=4,
                        scroll="auto",
                    ),
                    expand=True,
                    alignment=ft.alignment.top_center,
                ),
                util_panel,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        expand=True,
        bgcolor=UX.BG,
    )

    return root
