import flet as ft
import flet.canvas as cv
from datetime import datetime
from collections import defaultdict

from app.db.transactions import (
    get_recent_transactions,
    get_transactions_for_analytics,
    get_category_spend,
)
from app.db.accounts import get_accounts
from app.db.categories import get_categories
from app.db.budgets import get_budgets


PALETTE = [
    ft.Colors.BLUE_400,
    ft.Colors.GREEN_400,
    ft.Colors.PURPLE_400,
    ft.Colors.ORANGE_400,
    ft.Colors.PINK_400,
    ft.Colors.CYAN_400,
    ft.Colors.AMBER_400,
    ft.Colors.TEAL_400,
    ft.Colors.INDIGO_400,
    ft.Colors.LIME_400,
]

INCOME_COLOR = ft.Colors.GREEN_400
EXPENSE_COLOR = ft.Colors.RED_400
AXIS_COLOR = ft.Colors.GREY_600
GRID_COLOR = ft.Colors.GREY_200


def _card(content, width=None, padding=18):
    return ft.Container(
        content,
        bgcolor=ft.Colors.WHITE,
        border_radius=18,
        padding=ft.padding.all(padding),
        width=width,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=18,
            color=ft.Colors.GREY_100,
            offset=ft.Offset(0, 6),
        ),
        margin=ft.margin.only(bottom=18),
    )


def build_category_bar_chart(cat_amounts: dict[str, float]) -> ft.Control:
    max_amount = max([abs(v) for v in cat_amounts.values()], default=0) or 1
    bar_height = 32
    bar_gap = 24
    left_label_x = 12
    bar_x = 150
    usable_width = 360
    top_offset = 18

    shapes: list[cv.Shape] = []
    for idx, (cat, amount) in enumerate(cat_amounts.items()):
        y = top_offset + idx * (bar_height + bar_gap)
        width_ratio = abs(amount) / max_amount
        bar_w = max(2, int(usable_width * width_ratio))
        color = PALETTE[idx % len(PALETTE)]
        shapes.append(
            cv.Rect(
                x=bar_x,
                y=y,
                width=usable_width,
                height=bar_height,
                paint=ft.Paint(color=ft.Colors.GREY_100),
            )
        )
        shapes.append(
            cv.Rect(
                x=bar_x,
                y=y,
                width=bar_w,
                height=bar_height,
                paint=ft.Paint(color=color),
            )
        )
        shapes.append(
            cv.Text(
                left_label_x,
                y + 9,
                cat,
                ft.TextStyle(
                    size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900
                ),
            )
        )
        shapes.append(
            cv.Text(
                bar_x + bar_w + 12,
                y + 9,
                f"{amount:.2f}",
                ft.TextStyle(size=15, weight=ft.FontWeight.BOLD, color=color),
            )
        )

    canvas_height = max(100, top_offset + len(cat_amounts) * (bar_height + bar_gap))
    canvas = cv.Canvas(width=560, height=canvas_height, shapes=shapes)
    return _card(
        ft.Column(
            [
                ft.Text(
                    "Category Breakdown",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_400,
                ),
                canvas,
            ],
            spacing=14,
        )
    )


def build_income_expense_line_chart(month_income, month_expense) -> ft.Control:
    width = 560
    height = 260
    margin_left = 55
    margin_bottom = 40
    margin_top = 20
    margin_right = 20

    months = sorted(
        set([m for m, _ in month_income] + [m for m, _ in month_expense]),
        key=lambda m: datetime.strptime(m, "%Y-%m"),
    )
    income_map = {m: v for m, v in month_income}
    expense_map = {m: v for m, v in month_expense}
    values = list(income_map.values()) + list(expense_map.values())
    max_val = max(values, default=0) or 1

    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    def x_pos(idx: int):
        if len(months) <= 1:
            return margin_left + plot_w // 2
        return margin_left + int(idx * (plot_w / (len(months) - 1)))

    def y_pos(value: float):
        ratio = value / max_val
        return margin_top + (plot_h - int(plot_h * ratio))

    shapes: list[cv.Shape] = []
    grid_steps = 5
    for i in range(grid_steps + 1):
        val = max_val * i / grid_steps
        y = y_pos(val)
        shapes.append(
            cv.Line(
                x1=margin_left,
                y1=y,
                x2=margin_left + plot_w,
                y2=y,
                paint=ft.Paint(color=GRID_COLOR),
            )
        )
        shapes.append(
            cv.Text(
                4,
                y - 8,
                f"{val:.0f}",
                ft.TextStyle(size=12, color=AXIS_COLOR),
            )
        )
    shapes.append(
        cv.Line(
            x1=margin_left,
            y1=margin_top,
            x2=margin_left,
            y2=margin_top + plot_h,
            paint=ft.Paint(color=AXIS_COLOR),
        )
    )
    shapes.append(
        cv.Line(
            x1=margin_left,
            y1=margin_top + plot_h,
            x2=margin_left + plot_w,
            y2=margin_top + plot_h,
            paint=ft.Paint(color=AXIS_COLOR),
        )
    )
    for idx, m in enumerate(months):
        x = x_pos(idx)
        shapes.append(
            cv.Text(
                x - 22,
                margin_top + plot_h + 10,
                m,
                ft.TextStyle(size=11, color=AXIS_COLOR),
            )
        )

    def plot_series(data_map: dict, color: str, upper=True):
        last_xy = None
        for idx, m in enumerate(months):
            val = data_map.get(m, 0)
            x = x_pos(idx)
            y = y_pos(val)
            shapes.append(
                cv.Circle(
                    x=x,
                    y=y,
                    radius=5,
                    paint=ft.Paint(color=color),
                )
            )
            if last_xy:
                shapes.append(
                    cv.Line(
                        x1=last_xy[0],
                        y1=last_xy[1],
                        x2=x,
                        y2=y,
                        paint=ft.Paint(color=color, stroke_width=3),
                    )
                )
            last_xy = (x, y)
            shapes.append(
                cv.Text(
                    x - 14,
                    y - 22 if upper else y + 10,
                    f"{val:.0f}",
                    ft.TextStyle(size=11, color=color, weight=ft.FontWeight.BOLD),
                )
            )

    plot_series(income_map, INCOME_COLOR, upper=True)
    plot_series(expense_map, EXPENSE_COLOR, upper=False)

    # Legend
    legend_y = margin_top - 8
    legend_items = [("Income", INCOME_COLOR), ("Expense", EXPENSE_COLOR)]
    lx = margin_left
    for label, c in legend_items:
        shapes.append(
            cv.Rect(x=lx, y=legend_y, width=18, height=10, paint=ft.Paint(color=c))
        )
        shapes.append(
            cv.Text(
                lx + 24,
                legend_y - 4,
                label,
                ft.TextStyle(size=12, color=ft.Colors.GREY_800),
            )
        )
        lx += 100

    canvas = cv.Canvas(width=width, height=height, shapes=shapes)
    return _card(
        ft.Column(
            [
                ft.Text(
                    "Income vs Expense (Monthly)",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PURPLE_400,
                ),
                canvas,
            ],
            spacing=14,
        )
    )


def build_budget_chart(budgets: list[dict], cat_dict: dict[int, str]) -> ft.Control:
    shapes: list[cv.Shape] = []
    bar_h = 26
    gap = 22
    bar_x = 160
    top = 16
    width_full = 340

    for idx, b in enumerate(budgets):
        spent = get_category_spend(b["category_id"], b["start_date"], b["end_date"])
        amount = b["amount"] or 0
        pct = min(spent / amount, 1.0) if amount > 0 else 0
        base_y = top + idx * (bar_h + gap)
        shapes.append(
            cv.Rect(
                x=bar_x,
                y=base_y,
                width=width_full,
                height=bar_h,
                paint=ft.Paint(color=ft.Colors.GREY_100),
            )
        )
        color = (
            ft.Colors.GREEN_400
            if pct < 0.9
            else (ft.Colors.ORANGE_400 if pct < 1.0 else ft.Colors.RED_400)
        )
        shapes.append(
            cv.Rect(
                x=bar_x,
                y=base_y,
                width=int(width_full * pct),
                height=bar_h,
                paint=ft.Paint(color=color),
            )
        )
        shapes.append(
            cv.Text(
                20,
                base_y + 7,
                cat_dict.get(b["category_id"], "Other"),
                ft.TextStyle(
                    size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900
                ),
            )
        )
        shapes.append(
            cv.Text(
                bar_x + 10,
                base_y + 6,
                f"{spent:.2f}/{amount:.2f}",
                ft.TextStyle(size=13, color=ft.Colors.WHITE if pct > 0.4 else color),
            )
        )
        shapes.append(
            cv.Text(
                bar_x + width_full + 12,
                base_y + 6,
                f"{int(pct * 100)}%",
                ft.TextStyle(size=13, weight=ft.FontWeight.BOLD, color=color),
            )
        )

    canvas_height = max(120, top + len(budgets) * (bar_h + gap))
    canvas = cv.Canvas(width=560, height=canvas_height, shapes=shapes)
    return _card(
        ft.Column(
            [
                ft.Text(
                    "Budget Utilization",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_400,
                ),
                canvas,
            ],
            spacing=14,
        )
    )


def build_kpi_row(txs: list[dict]) -> ft.Control:
    total_income = sum(float(t["amount"]) for t in txs if float(t["amount"]) > 0)
    total_expense = sum(abs(float(t["amount"])) for t in txs if float(t["amount"]) < 0)
    net = total_income - total_expense
    kpis = [
        ("Income", f"{total_income:.2f}", ft.Colors.GREEN_400),
        ("Expense", f"{total_expense:.2f}", ft.Colors.RED_400),
        ("Net", f"{net:.2f}", ft.Colors.BLUE_400 if net >= 0 else ft.Colors.RED_400),
        ("Transactions", f"{len(txs)}", ft.Colors.PURPLE_400),
    ]
    cards = []
    for title, value, color in kpis:
        cards.append(
            ft.Container(
                ft.Column(
                    [
                        ft.Text(title, size=14, color=ft.Colors.GREY_700),
                        ft.Text(
                            value,
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=color,
                        ),
                    ],
                    spacing=4,
                ),
                bgcolor=ft.Colors.WHITE,
                padding=ft.padding.all(16),
                border_radius=18,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=14,
                    color=ft.Colors.GREY_100,
                    offset=ft.Offset(0, 4),
                ),
                width=150,
            )
        )
    return ft.Row(cards, spacing=18, wrap=False)


def dashboard_page(page: ft.Page):
    accounts = get_accounts()
    balances_cards = [
        ft.Container(
            ft.Column(
                [
                    ft.Text(
                        acc.name,
                        style="titleMedium",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_800,
                    ),
                    *[
                        ft.Text(
                            f"{b['currency']}: {float(b['balance']):.2f}",
                            style="bodyMedium",
                            color=(
                                ft.Colors.BLUE_400
                                if float(b["balance"]) >= 0
                                else ft.Colors.RED_400
                            ),
                            weight=ft.FontWeight.BOLD,
                        )
                        for b in acc.balances
                    ],
                ],
                spacing=6,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=18,
            padding=ft.padding.all(18),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=18,
                color=ft.Colors.GREY_100,
                offset=ft.Offset(0, 6),
            ),
            width=210,
            margin=ft.margin.only(right=20, bottom=18),
        )
        for acc in accounts
    ]
    balances_row = ft.Row(balances_cards, spacing=0, wrap=True)

    txs = get_transactions_for_analytics()
    categories = get_categories()
    cat_dict = {c["id"]: c["name"] for c in categories}

    cat_amounts = defaultdict(float)
    for t in txs:
        cat = cat_dict.get(t["category_id"], "Other")
        cat_amounts[cat] += float(t["amount"])

    month_income = defaultdict(float)
    month_expense = defaultdict(float)
    for t in txs:
        dt = datetime.strptime(t["date"], "%Y-%m-%d")
        key = dt.strftime("%Y-%m")
        amt = float(t["amount"])
        if amt > 0:
            month_income[key] += amt
        else:
            month_expense[key] += abs(amt)

    income_series = sorted(month_income.items(), key=lambda x: x[0])
    expense_series = sorted(month_expense.items(), key=lambda x: x[0])
    budgets = get_budgets()

    kpi_row = build_kpi_row(txs)
    category_chart = build_category_bar_chart(dict(cat_amounts))
    line_chart = build_income_expense_line_chart(income_series, expense_series)
    budget_chart = build_budget_chart(budgets, cat_dict)

    recent = get_recent_transactions(6)
    recent_rows = (
        [
            ft.Container(
                ft.Row(
                    [
                        ft.Text(r.date, width=90, color=ft.Colors.GREY_700),
                        ft.Text(
                            f"{r.amount:.2f} {r.currency}",
                            width=120,
                            color=(
                                ft.Colors.GREEN_400
                                if r.amount > 0
                                else ft.Colors.RED_400
                            ),
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            getattr(r, "category_name", "Other"),
                            width=120,
                            color=ft.Colors.GREY_800,
                        ),
                        ft.Text(
                            f"Acc {r.account_id}",
                            width=80,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                    spacing=12,
                ),
                padding=ft.padding.symmetric(vertical=6, horizontal=8),
                bgcolor=ft.Colors.GREY_50,
                border_radius=10,
                margin=ft.margin.only(bottom=6),
            )
            for r in recent
        ]
        if recent
        else [
            ft.Text(
                "No recent transactions.",
                italic=True,
                color=ft.Colors.GREY_600,
            )
        ]
    )
    recent_section = _card(
        ft.Column(
            [
                ft.Text(
                    "Recent Transactions",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                *recent_rows,
            ],
            spacing=10,
        )
    )

    left_col = ft.Column(
        [
            _card(
                ft.Column(
                    [
                        ft.Text(
                            "Key Metrics",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_800,
                        ),
                        kpi_row,
                    ],
                    spacing=16,
                )
            ),
            category_chart,
            budget_chart,
        ],
        spacing=8,
        expand=1,
    )

    right_col = ft.Column(
        [
            line_chart,
            recent_section,
        ],
        spacing=8,
        expand=1,
    )

    # SCROLLABLE AREA (ListView)
    scroll_view = ft.ListView(
        expand=True,
        spacing=26,
        padding=ft.padding.all(0),
        controls=[
            ft.Text(
                "Dashboard",
                style="headlineSmall",
                size=34,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_400,
            ),
            ft.Divider(height=2, color=ft.Colors.GREY_100),
            ft.Text(
                "Account Balances",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREY_800,
            ),
            balances_row,
            ft.Divider(height=2, color=ft.Colors.GREY_100),
            ft.ResponsiveRow(
                [
                    ft.Container(left_col, col={"xs": 12, "md": 6}),
                    ft.Container(right_col, col={"xs": 12, "md": 6}),
                ],
                run_spacing=20,
            ),
        ],
    )

    return ft.Container(
        scroll_view,
        padding=ft.padding.all(26),
        bgcolor=ft.Colors.GREY_50,
        expand=True,
    )
