import datetime
import flet as ft
from app.db.categories import get_categories
from app.db.budgets import get_budgets, add_budget, update_budget, delete_budget
from app.db.transactions import get_category_spend


# Design Tokens / Theme Layer
class UX:
    BG = ft.Colors.GREY_50
    SURFACE = ft.Colors.WHITE
    SURFACE_ALT = ft.Colors.GREY_100
    BORDER = ft.Colors.GREY_300
    TEXT = ft.Colors.GREY_900
    MUTED = ft.Colors.GREY_600
    ACCENT = ft.Colors.BLUE_400
    ACCENT_ALT = ft.Colors.BLUE_600
    SUCCESS = ft.Colors.GREEN_400
    WARNING = ft.Colors.AMBER_400
    WARNING_ALT = ft.Colors.ORANGE_400
    DANGER = ft.Colors.RED_400
    SHADOW = ft.BoxShadow(
        spread_radius=1,
        blur_radius=18,
        color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        offset=ft.Offset(0, 6),
    )
    R_SM = 8
    R_MD = 14
    R_LG = 20
    R_XL = 26


def budgets_page(page: ft.Page):
    page.bgcolor = UX.BG
    page.padding = 0

    # ------------- Data & Lookup -------------
    categories = get_categories()
    category_map = {c["id"]: c["name"] for c in categories}

    # ------------- Helpers -------------
    def today():
        return datetime.date.today()

    def month_range(ref: datetime.date):
        start = ref.replace(day=1)
        nxt = (start + datetime.timedelta(days=32)).replace(day=1)
        end = nxt - datetime.timedelta(days=1)
        return start, end

    def week_range(ref: datetime.date):
        start = ref - datetime.timedelta(days=ref.weekday())
        end = start + datetime.timedelta(days=6)
        return start, end

    def fmt(d: datetime.date | str):
        if isinstance(d, datetime.date):
            return d.isoformat()
        return d

    def parse_float(val: str, default=0.0):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def snack(msg: str, color=UX.ACCENT):
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        if page:
            page.update()

    # ------------- Add Form State -------------
    period_choices = [
        ("monthly", "Monthly"),
        ("weekly", "Weekly"),
        ("custom", "Custom"),
    ]

    category_field = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in categories],
        width=210,
    )
    period_field = ft.Dropdown(
        label="Period",
        options=[ft.dropdown.Option(v, lbl) for v, lbl in period_choices],
        width=150,
    )
    amount_field = ft.TextField(
        label="Budget Amount",
        keyboard_type="number",
        width=150,
        tooltip="Positive number (e.g. 250.00)",
    )
    start_field = ft.TextField(label="Start (YYYY-MM-DD)", width=150, visible=False)
    end_field = ft.TextField(label="End (YYYY-MM-DD)", width=150, visible=False)
    form_feedback = ft.Text("", color=UX.DANGER, size=12)

    # Quick fill buttons
    def set_this_month(e):
        s, e_ = month_range(today())
        start_field.value = fmt(s)
        end_field.value = fmt(e_)
        start_field.visible = True
        end_field.visible = True
        period_field.value = "custom"
        update_form_visibility()

    def set_this_week(e):
        s, e_ = week_range(today())
        start_field.value = fmt(s)
        end_field.value = fmt(e_)
        start_field.visible = True
        end_field.visible = True
        period_field.value = "custom"
        update_form_visibility()

    quick_row = ft.Row(
        [
            ft.TextButton(
                "This Month", icon=ft.Icons.CALENDAR_MONTH, on_click=set_this_month
            ),
            ft.TextButton(
                "This Week", icon=ft.Icons.DATE_RANGE, on_click=set_this_week
            ),
        ],
        spacing=4,
    )

    def update_form_visibility():
        p = period_field.value
        if p == "custom":
            start_field.visible = True
            end_field.visible = True
            start_field.disabled = False
            end_field.disabled = False
        else:
            if p == "monthly":
                s, e_ = month_range(today())
            elif p == "weekly":
                s, e_ = week_range(today())
            else:
                s, e_ = today(), today()
            start_field.value = fmt(s)
            end_field.value = fmt(e_)
            start_field.visible = True
            end_field.visible = True
            start_field.disabled = True
            end_field.disabled = True
        page.update()

    period_field.on_change = lambda e: update_form_visibility()

    # ------------- Edit Dialog -------------
    edit_dialog = ft.AlertDialog(modal=True)
    edit_budget_id = [None]
    edit_category = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in categories],
        width=210,
    )
    edit_period = ft.Dropdown(
        label="Period",
        options=[ft.dropdown.Option(v, lbl) for v, lbl in period_choices],
        width=150,
    )
    edit_amount = ft.TextField(label="Amount", keyboard_type="number", width=150)
    edit_start = ft.TextField(label="Start (YYYY-MM-DD)", width=150)
    edit_end = ft.TextField(label="End (YYYY-MM-DD)", width=150)
    edit_feedback = ft.Text("", color=UX.DANGER, size=12)

    def open_edit(budget: dict):
        edit_budget_id[0] = budget["id"]
        edit_category.value = str(budget["category_id"])
        edit_period.value = budget["period"]
        edit_amount.value = f"{budget['amount']:.2f}"
        edit_start.value = budget["start_date"]
        edit_end.value = budget["end_date"]
        edit_feedback.value = ""
        page.dialog = edit_dialog
        edit_dialog.open = True
        page.update()

    def close_edit(e=None):
        edit_dialog.open = False
        page.update()

    def save_edit(e):
        try:
            cat_id = int(edit_category.value)
            per = edit_period.value
            amt = parse_float(edit_amount.value, 0.0)
            s_val = edit_start.value.strip()
            e_val = edit_end.value.strip()
            if per in ("monthly", "weekly") and (not s_val or not e_val):
                if per == "monthly":
                    s, ee = month_range(today())
                else:
                    s, ee = week_range(today())
                s_val, e_val = fmt(s), fmt(ee)
            if amt <= 0:
                edit_feedback.value = "Amount must be > 0"
                page.update()
                return
            update_budget(
                edit_budget_id[0],
                category_id=cat_id,
                period=per,
                amount=amt,
                start_date=s_val,
                end_date=e_val,
            )
            close_edit()
            refresh_budgets()
            snack("Budget updated", UX.SUCCESS)
        except Exception as ex:
            edit_feedback.value = f"Error: {ex}"
            page.update()

    edit_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("Edit Budget", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([edit_category, edit_period, edit_amount], spacing=14),
                ft.Row([edit_start, edit_end], spacing=14),
                edit_feedback,
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Save",
                            icon=ft.Icons.SAVE,
                            bgcolor=UX.ACCENT,
                            color=ft.Colors.WHITE,
                            on_click=save_edit,
                        ),
                        ft.TextButton("Cancel", on_click=close_edit),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=16,
        ),
        width=680,
        padding=24,
        bgcolor=UX.SURFACE,
        border_radius=UX.R_LG,
    )
    page.overlay.append(edit_dialog)

    # ------------- Budget List + Filtering -------------
    budgets_container = ft.Column(spacing=18, width=1000)
    filter_period = ft.Dropdown(
        label="Filter Period",
        width=170,
        options=[ft.dropdown.Option("all", "All")]
        + [ft.dropdown.Option(v, lbl) for v, lbl in period_choices],
        value="all",
    )

    def badge(percent: float):
        if percent >= 1:
            txt, col, bg = "Exceeded", UX.DANGER, ft.Colors.RED_50
        elif percent >= 0.85:
            txt, col, bg = "Critical", UX.WARNING_ALT, ft.Colors.ORANGE_50
        elif percent >= 0.7:
            txt, col, bg = "Warning", UX.WARNING, ft.Colors.AMBER_50
        else:
            txt, col, bg = "On Track", UX.SUCCESS, ft.Colors.GREEN_50
        return ft.Container(
            ft.Text(txt, size=11, weight=ft.FontWeight.BOLD, color=col),
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=UX.R_SM,
            bgcolor=bg,
        )

    def progress_color(percent: float):
        if percent >= 1:
            return UX.DANGER
        elif percent >= 0.85:
            return UX.WARNING_ALT
        elif percent >= 0.7:
            return UX.WARNING
        return UX.SUCCESS

    def show_overshoot_alert(cat_name, spent_display, amount):
        dialog = ft.AlertDialog(
            title=ft.Text("Budget Limit Exceeded"),
            content=ft.Text(f"{cat_name}\nSpent {spent_display:.2f} of {amount:.2f}"),
            actions=[ft.TextButton("OK", on_click=lambda e: close_alert())],
            modal=True,
            open=True,
        )
        page.dialog = dialog
        page.update()

    def close_alert():
        if page.dialog:
            page.dialog.open = False
            page.update()

    def delete_budget_ui(budget_id):
        delete_budget(budget_id)
        refresh_budgets()
        snack("Budget deleted", UX.DANGER)

    def build_budget_card(
        b: dict, spent_positive: float, percent: float, raw_signed: float
    ):
        color = progress_color(percent)
        pct_text = int(min(percent, 1) * 100)
        name = category_map.get(b["category_id"], "Unknown")
        per_label = b["period"].capitalize()
        badge_ctrl = badge(percent)

        prog_stack = ft.Stack(
            [
                ft.ProgressBar(
                    value=min(percent, 1.0),
                    bgcolor=ft.Colors.GREY_200,
                    color=color,
                    width=430,
                    height=20,
                    border_radius=UX.R_SM,
                ),
                ft.Text(
                    f"{pct_text}%  {spent_positive:.2f}/{b['amount']:.2f}",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=color,
                    top=2,
                    left=10,
                ),
            ]
        )

        meta = ft.Text(
            f"{b['start_date']}  →  {b['end_date']}",
            size=11,
            color=UX.MUTED,
        )

        # Remaining is always against positive spent
        remaining = max(b["amount"] - spent_positive, 0)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.PIE_CHART, color=color, size=24),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                f"{name}",
                                                size=16,
                                                weight=ft.FontWeight.W_600,
                                                color=UX.TEXT,
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Container(
                                                        ft.Text(
                                                            per_label,
                                                            size=10,
                                                            weight=ft.FontWeight.BOLD,
                                                            color=UX.ACCENT,
                                                        ),
                                                        bgcolor=ft.Colors.BLUE_50,
                                                        padding=ft.padding.symmetric(
                                                            horizontal=8, vertical=2
                                                        ),
                                                        border_radius=UX.R_SM,
                                                    ),
                                                    badge_ctrl,
                                                ],
                                                spacing=6,
                                            ),
                                        ],
                                        spacing=3,
                                    ),
                                ],
                                spacing=12,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Edit",
                                        on_click=lambda e, bb=b: open_edit(bb),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_100,
                                            color=UX.ACCENT,
                                            shape=ft.RoundedRectangleBorder(
                                                radius=UX.R_SM
                                            ),
                                        ),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_ROUNDED,
                                        tooltip="Delete",
                                        on_click=lambda e,
                                        bid=b["id"]: delete_budget_ui(bid),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_100,
                                            color=UX.DANGER,
                                            shape=ft.RoundedRectangleBorder(
                                                radius=UX.R_SM
                                            ),
                                        ),
                                    ),
                                ],
                                spacing=6,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    prog_stack,
                    ft.Row(
                        [
                            meta,
                            ft.Text(
                                f"Remaining: {remaining:.2f}",
                                size=11,
                                color=UX.MUTED,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=14,
            ),
            padding=ft.padding.all(20),
            bgcolor=UX.SURFACE,
            border_radius=UX.R_LG,
            shadow=UX.SHADOW,
        )

    def refresh_budgets():
        budgets_container.controls.clear()
        budgets = get_budgets()
        selected_period = filter_period.value
        overshoot_shown = False

        budgets.sort(key=lambda x: (x["end_date"], x["category_id"]))

        for b in budgets:
            if (
                selected_period
                and selected_period != "all"
                and b["period"] != selected_period
            ):
                continue
            raw_signed = get_category_spend(
                b["category_id"], b["start_date"], b["end_date"]
            )
            # Convert signed sum to positive magnitude for budget comparison
            spent_positive = abs(raw_signed)
            percent = spent_positive / b["amount"] if b["amount"] > 0 else 0
            if percent >= 1 and not overshoot_shown:
                show_overshoot_alert(
                    category_map.get(b["category_id"], "Unknown"),
                    spent_positive,
                    b["amount"],
                )
                overshoot_shown = True
            card = build_budget_card(b, spent_positive, percent, raw_signed)
            budgets_container.controls.append(card)

        if not budgets_container.controls:
            budgets_container.controls.append(
                ft.Container(
                    ft.Text(
                        "No budgets match current filter.", color=UX.MUTED, size=14
                    ),
                    padding=30,
                    alignment=ft.alignment.center,
                    bgcolor=UX.SURFACE,
                    border_radius=UX.R_LG,
                )
            )
        if budgets_container.page:
            budgets_container.update()

    filter_period.on_change = lambda e: refresh_budgets()

    # ------------- Add Budget Logic -------------
    def submit_add(e):
        form_feedback.value = ""
        try:
            if not category_field.value:
                form_feedback.value = "Select a category."
                page.update()
                return
            if not period_field.value:
                form_feedback.value = "Select a period."
                page.update()
                return
            amount = parse_float(amount_field.value, -1)
            if amount <= 0:
                form_feedback.value = "Amount must be greater than 0."
                page.update()
                return

            per = period_field.value
            if per == "custom":
                if not start_field.value or not end_field.value:
                    form_feedback.value = (
                        "Provide start and end dates for custom period."
                    )
                    page.update()
                    return
                s_val = start_field.value.strip()
                e_val = end_field.value.strip()
            else:
                s_val = start_field.value
                e_val = end_field.value

            add_budget(int(category_field.value), per, amount, s_val, e_val)
            snack("Budget added", UX.SUCCESS)
            amount_field.value = ""
            form_feedback.value = ""
            refresh_budgets()
            page.update()
        except Exception as ex:
            form_feedback.value = f"Error: {ex}"
            page.update()

    add_btn = ft.ElevatedButton(
        "Add Budget",
        icon=ft.Icons.ADD_CIRCLE,
        bgcolor=UX.ACCENT,
        color=ft.Colors.WHITE,
        on_click=submit_add,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=UX.R_MD),
            elevation=4,
        ),
        height=44,
    )

    add_form_card = ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Create Budget", size=22, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        filter_period,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(
                    height=18, color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK)
                ),
                ft.ResponsiveRow(
                    [
                        ft.Container(category_field, col={"xs": 12, "md": 3}),
                        ft.Container(period_field, col={"xs": 6, "md": 2}),
                        ft.Container(amount_field, col={"xs": 6, "md": 2}),
                        ft.Container(start_field, col={"xs": 6, "md": 2}),
                        ft.Container(end_field, col={"xs": 6, "md": 2}),
                        ft.Container(add_btn, col={"xs": 12, "md": 1}),
                    ],
                    run_spacing=12,
                ),
                ft.Row(
                    [
                        quick_row,
                        ft.Container(expand=True),
                        form_feedback,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
            ],
            spacing=18,
        ),
        width=1000,
        padding=ft.padding.all(28),
        bgcolor=UX.SURFACE,
        border_radius=UX.R_XL,
        shadow=UX.SHADOW,
        margin=ft.margin.only(top=30, bottom=12),
    )

    # Initial load
    update_form_visibility()
    refresh_budgets()

    root = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Budgets Overview",
                    size=30,
                    weight=ft.FontWeight.W_600,
                    color=UX.TEXT,
                ),
                add_form_card,
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                "Active Budgets",
                                size=22,
                                weight=ft.FontWeight.W_600,
                                color=UX.TEXT,
                            ),
                            budgets_container,
                        ],
                        spacing=22,
                    ),
                    width=1000,
                    padding=ft.padding.only(bottom=40),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll="auto",
            spacing=8,
        ),
        expand=True,
        alignment=ft.alignment.top_center,
        bgcolor=UX.BG,
    )

    return root
