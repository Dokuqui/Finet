import flet as ft
from app.db.categories import get_categories
from app.db.budgets import (
    get_budgets,
    add_budget,
    update_budget,
    delete_budget,
)
from app.db.transactions import get_category_spend
import datetime


def budgets_page(page: ft.Page):
    categories = get_categories()
    category_dict = {cat["id"]: cat["name"] for cat in categories}

    # Input fields
    category_field = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(str(cat["id"]), cat["name"]) for cat in categories],
        width=200,
    )
    period_field = ft.Dropdown(
        label="Period",
        options=[
            ft.dropdown.Option("monthly", "Monthly"),
            ft.dropdown.Option("weekly", "Weekly"),
            ft.dropdown.Option("custom", "Custom"),
        ],
        width=120,
    )
    amount_field = ft.TextField(
        label="Budget Amount", keyboard_type="number", width=120
    )
    start_date_field = ft.TextField(label="Start Date (YYYY-MM-DD)", width=120)
    end_date_field = ft.TextField(label="End Date (YYYY-MM-DD)", width=120)
    feedback_text = ft.Text("", color=ft.Colors.RED_400)

    # Edit Dialog
    edit_dialog = ft.AlertDialog(modal=True)
    edit_category_field = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(str(cat["id"]), cat["name"]) for cat in categories],
        width=200,
    )
    edit_period_field = ft.Dropdown(
        label="Period",
        options=[
            ft.dropdown.Option("monthly", "Monthly"),
            ft.dropdown.Option("weekly", "Weekly"),
            ft.dropdown.Option("custom", "Custom"),
        ],
        width=120,
    )
    edit_amount_field = ft.TextField(
        label="Budget Amount", keyboard_type="number", width=120
    )
    edit_start_date_field = ft.TextField(label="Start Date (YYYY-MM-DD)", width=120)
    edit_end_date_field = ft.TextField(label="End Date (YYYY-MM-DD)", width=120)
    edit_feedback = ft.Text("", color=ft.Colors.RED_400)
    editing_budget_id = [None]

    def open_edit_dialog(budget):
        editing_budget_id[0] = budget["id"]
        edit_category_field.value = str(budget["category_id"])
        edit_period_field.value = budget["period"]
        edit_amount_field.value = str(budget["amount"])
        edit_start_date_field.value = budget["start_date"]
        edit_end_date_field.value = budget["end_date"]
        edit_feedback.value = ""
        edit_dialog.open = True
        page.dialog = edit_dialog
        page.update()

    def close_edit_dialog(e=None):
        edit_dialog.open = False
        page.update()

    def save_edit_budget(e):
        try:
            cat_id = int(edit_category_field.value)
            period = edit_period_field.value
            amount = float(edit_amount_field.value)
            start_date = edit_start_date_field.value.strip()
            end_date = edit_end_date_field.value.strip()
            today = datetime.date.today()
            if period == "monthly" and (not start_date or not end_date):
                start_date = today.replace(day=1)
                end_date = (start_date + datetime.timedelta(days=32)).replace(
                    day=1
                ) - datetime.timedelta(days=1)
            elif period == "weekly" and (not start_date or not end_date):
                start_date = today - datetime.timedelta(days=today.weekday())
                end_date = start_date + datetime.timedelta(days=6)
            update_budget(
                editing_budget_id[0],
                category_id=cat_id,
                period=period,
                amount=amount,
                start_date=str(start_date),
                end_date=str(end_date),
            )
            edit_feedback.value = "Budget updated!"
            close_edit_dialog()
            refresh_budgets()
        except Exception as ex:
            edit_feedback.value = f"Error: {ex}"
            page.update()

    edit_dialog.content = ft.Container(
        ft.Column(
            [
                ft.Text("Edit Budget", style="headlineSmall", size=18),
                edit_category_field,
                edit_period_field,
                edit_amount_field,
                edit_start_date_field,
                edit_end_date_field,
                ft.Row(
                    [
                        ft.ElevatedButton("Save", on_click=save_edit_budget, width=90),
                        ft.TextButton("Cancel", on_click=close_edit_dialog, width=90),
                        edit_feedback,
                    ],
                    spacing=10,
                ),
            ],
            spacing=12,
        ),
        width=340,
        padding=18,
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
    )
    page.overlay.append(edit_dialog)

    def on_add_budget(e):
        try:
            cat_id = int(category_field.value)
            period = period_field.value
            amount = float(amount_field.value)
            start_date = start_date_field.value.strip()
            end_date = end_date_field.value.strip()
            today = datetime.date.today()
            if period == "monthly" and (not start_date or not end_date):
                start_date = today.replace(day=1)
                end_date = (start_date + datetime.timedelta(days=32)).replace(
                    day=1
                ) - datetime.timedelta(days=1)
            elif period == "weekly" and (not start_date or not end_date):
                start_date = today - datetime.timedelta(days=today.weekday())
                end_date = start_date + datetime.timedelta(days=6)
            elif period == "custom":
                if not start_date or not end_date:
                    feedback_text.value = (
                        "Please provide both start and end dates for custom period."
                    )
                    page.update()
                    return
            add_budget(cat_id, period, amount, str(start_date), str(end_date))
            feedback_text.value = "Budget added!"
            refresh_budgets()
        except Exception as ex:
            feedback_text.value = f"Error: {ex}"
        page.update()

    add_btn = ft.ElevatedButton(
        "Add Budget",
        icon=ft.Icons.ADD,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_400,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=14),
            elevation=2,
        ),
        width=120,
        height=36,
        on_click=on_add_budget,
    )

    def delete_budget_ui(budget_id):
        delete_budget(budget_id)
        feedback_text.value = "Budget deleted!"
        refresh_budgets()
        page.update()

    # --- Notification Popups ---
    def show_budget_alert(category_name, spent, budget):
        dialog = ft.AlertDialog(
            title=ft.Text("Budget Limit Exceeded!"),
            content=ft.Text(
                f"You have exceeded your budget for {category_name}.\n"
                f"Spent: {spent:.2f} / Budget: {budget:.2f}"
            ),
            actions=[ft.TextButton("OK", on_click=lambda e: close_budget_alert())],
            modal=True,
            open=True,
        )
        page.dialog = dialog
        page.update()

    def close_budget_alert():
        page.dialog.open = False
        page.update()

    budgets_list = ft.Column()

    def budget_status_badge(percent):
        if percent >= 1.0:
            return ft.Container(
                ft.Text(
                    "Exceeded",
                    color=ft.Colors.RED_400,
                    size=13,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=ft.Colors.RED_50,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
            )
        elif percent >= 0.9:
            return ft.Container(
                ft.Text(
                    "Nearing",
                    color=ft.Colors.ORANGE_400,
                    size=13,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
            )
        else:
            return ft.Container(
                ft.Text(
                    "On Track",
                    color=ft.Colors.GREEN_400,
                    size=13,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=ft.Colors.GREEN_50,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
            )

    def refresh_budgets():
        budgets_list.controls.clear()
        budgets = get_budgets()
        # Track if any exceeded popups shown this refresh
        popup_shown = False
        for b in budgets:
            spent = get_category_spend(b["category_id"], b["start_date"], b["end_date"])
            percent = min(spent / b["amount"], 1.0) if b["amount"] > 0 else 0
            color = ft.Colors.GREEN_400
            status_badge = budget_status_badge(percent)
            # Only show one exceeded popup per refresh
            if percent >= 1.0 and not popup_shown:
                color = ft.Colors.RED_400
                show_budget_alert(
                    category_dict.get(b["category_id"], "Unknown"), spent, b["amount"]
                )
                popup_shown = True
            elif percent >= 0.9 and not popup_shown:
                color = ft.Colors.ORANGE_400
                # Optional: show nearing alert as snack bar
                page.snack_bar = ft.SnackBar(
                    ft.Text(
                        f"Nearing budget limit for {category_dict.get(b['category_id'], 'Unknown')}.",
                        color=color,
                    )
                )
                page.update()
                popup_shown = True

            controls = [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.PIE_CHART, color=color, size=22),
                        ft.Text(
                            f"{category_dict.get(b['category_id'], 'Unknown')} ({b['period'].capitalize()})",
                            style="headlineSmall",
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_900,
                        ),
                        status_badge,
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Edit",
                                    on_click=lambda e, b=b: open_edit_dialog(b),
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.GREY_50,
                                        color=ft.Colors.BLUE_400,
                                        shape=ft.RoundedRectangleBorder(radius=14),
                                    ),
                                    width=28,
                                    height=28,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Delete",
                                    on_click=lambda e, b_id=b["id"]: delete_budget_ui(
                                        b_id
                                    ),
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.GREY_50,
                                        color=ft.Colors.RED_400,
                                        shape=ft.RoundedRectangleBorder(radius=14),
                                    ),
                                    width=28,
                                    height=28,
                                ),
                            ],
                            spacing=6,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(
                    f"Budget: {b['amount']:.2f} | Spent: {spent:.2f} | Period: {b['start_date']} to {b['end_date']}",
                    style="bodyMedium",
                    color=ft.Colors.GREY_700,
                ),
                ft.Container(
                    ft.Stack(
                        [
                            ft.ProgressBar(
                                value=percent,
                                color=color,
                                bgcolor=ft.Colors.GREY_200,
                                width=350,
                                height=18,
                                border_radius=9,
                            ),
                            ft.Text(
                                f"{int(percent * 100)}% ({spent:.2f}/{b['amount']:.2f})",
                                color=color,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                left=10,
                                top=2,
                            ),
                        ]
                    ),
                    margin=ft.margin.only(top=10, bottom=2),
                ),
            ]
            budgets_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        ft.Column(controls, spacing=10),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=18,
                        padding=ft.padding.all(24),
                        margin=ft.margin.symmetric(vertical=10),
                        shadow=ft.BoxShadow(
                            spread_radius=2,
                            blur_radius=16,
                            color=ft.Colors.GREY_100,
                            offset=ft.Offset(0, 6),
                        ),
                    ),
                    elevation=0,
                )
            )
        page.update()

    refresh_budgets()

    return ft.Column(
        [
            ft.Text(
                "Budgets Overview",
                style="headlineSmall",
                size=32,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Container(
                ft.Row(
                    [
                        category_field,
                        period_field,
                        amount_field,
                        start_date_field,
                        end_date_field,
                        add_btn,
                    ],
                    spacing=18,
                ),
                padding=ft.padding.all(18),
                bgcolor=ft.Colors.GREY_50,
                border_radius=14,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=8,
                    color=ft.Colors.GREY_100,
                    offset=ft.Offset(0, 2),
                ),
                margin=ft.margin.only(bottom=18),
            ),
            feedback_text,
            ft.Divider(),
            budgets_list,
        ],
        spacing=24,
    )
