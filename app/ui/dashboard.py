import flet as ft
import flet.canvas as cv
from datetime import datetime, timedelta
from collections import defaultdict
import math

from app.db.transactions import (
    get_recent_transactions,
    get_transactions_for_analytics,
    get_category_spend,
)
from app.db.accounts import get_accounts
from app.db.categories import get_categories
from app.db.budgets import get_budgets

# ============================================================
# THEME & DESIGN SYSTEM
# ============================================================


class Theme:
    # Core palette (light mode)
    BG = ft.Colors.GREY_50
    SURFACE = ft.Colors.WHITE
    SURFACE_SUBTLE = ft.Colors.GREY_100
    BORDER = ft.Colors.GREY_200
    TEXT = ft.Colors.GREY_900
    TEXT_MUTED = ft.Colors.GREY_600
    ACCENT = ft.Colors.BLUE_500
    ACCENT_ALT = ft.Colors.INDIGO_400
    POSITIVE = ft.Colors.GREEN_400
    NEGATIVE = ft.Colors.RED_400
    WARNING = ft.Colors.ORANGE_400
    NEUTRAL = ft.Colors.GREY_400
    INFO = ft.Colors.CYAN_400
    PURPLE = ft.Colors.PURPLE_400
    AMBER = ft.Colors.AMBER_400

    # Radii
    R_SM = 8
    R_MD = 14
    R_LG = 20
    R_XL = 26

    # Shadows
    SHADOW_LIGHT = ft.BoxShadow(
        spread_radius=1,
        blur_radius=18,
        color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
        offset=ft.Offset(0, 6),
    )
    SHADOW_SOFT = ft.BoxShadow(
        spread_radius=1,
        blur_radius=12,
        color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
        offset=ft.Offset(0, 4),
    )

    CHART_COLORS = [
        ft.Colors.BLUE_400,
        ft.Colors.GREEN_400,
        ft.Colors.PURPLE_400,
        ft.Colors.ORANGE_400,
        ft.Colors.PINK_400,
        ft.Colors.CYAN_400,
        ft.Colors.AMBER_400,
        ft.Colors.TEAL_400,
        ft.Colors.INDIGO_400,
        ft.Colors.LIME_500,
    ]


# (Optional future) toggle to dark mode:
def apply_dark_mode(t: Theme):
    # Example alt palette (not wired to UI yet)
    t.BG = ft.Colors.GREY_900
    t.SURFACE = ft.Colors.GREY_800
    t.SURFACE_SUBTLE = ft.Colors.GREY_700
    t.TEXT = ft.Colors.GREY_50
    t.TEXT_MUTED = ft.Colors.GREY_400
    t.BORDER = ft.Colors.GREY_600


THEME = Theme()

TIMEFRAME_OPTIONS = [
    ("30D", "Last 30 Days"),
    ("90D", "Last 90 Days"),
    ("YTD", "Year-To-Date"),
    ("ALL", "All Time"),
]

# ============================================================
# UTILS
# ============================================================


def fmt_number(val: float, decimals: int = 2):
    try:
        return f"{val:,.{decimals}f}"
    except Exception:
        return "0.00"


def month_key(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m")
    except Exception:
        return "0000-00"


def filter_transactions_by_timeframe(transactions: list[dict], code: str) -> list[dict]:
    if not transactions:
        return []
    if code == "ALL":
        return transactions
    today = datetime.today().date()
    if code == "30D":
        start = today - timedelta(days=30)
    elif code == "90D":
        start = today - timedelta(days=90)
    elif code == "YTD":
        start = datetime(today.year, 1, 1).date()
    else:
        return transactions
    res = []
    for t in transactions:
        try:
            d = datetime.strptime(t["date"], "%Y-%m-%d").date()
            if d >= start:
                res.append(t)
        except Exception:
            pass
    return res


def empty_state(title: str, subtitle: str = "No data available"):
    return ft.Container(
        ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=THEME.TEXT),
                ft.Text(subtitle, size=12, color=THEME.TEXT_MUTED),
            ],
            spacing=4,
        ),
        padding=ft.padding.all(28),
        bgcolor=THEME.SURFACE_SUBTLE,
        border_radius=THEME.R_LG,
    )


# ============================================================
# CARD COMPONENT
# ============================================================


def Card(
    *children,
    title: str | None = None,
    subtitle: str | None = None,
    icon: str | None = None,
    width=None,
    padding=20,
    gap=16,
    header_extra: ft.Control | None = None,
    variant: str = "default",
) -> ft.Control:
    if variant == "accent":
        bg = ft.Colors.with_opacity(0.06, THEME.ACCENT)
    elif variant == "subtle":
        bg = THEME.SURFACE_SUBTLE
    else:
        bg = THEME.SURFACE

    header_controls = []
    if title:
        row_items = []
        if icon:
            row_items.append(
                ft.Container(
                    ft.Icon(icon, size=20, color=THEME.ACCENT),
                    width=34,
                    height=34,
                    bgcolor=ft.Colors.with_opacity(0.12, THEME.ACCENT),
                    alignment=ft.alignment.center,
                    border_radius=THEME.R_MD,
                )
            )
        txt_col = [
            ft.Text(title, size=17, weight=ft.FontWeight.W_600, color=THEME.TEXT),
        ]
        if subtitle:
            txt_col.append(ft.Text(subtitle, size=11, color=THEME.TEXT_MUTED))
        row_items.append(ft.Column(txt_col, spacing=2))
        if header_extra:
            row_items.append(ft.Container(expand=True))
            row_items.append(header_extra)
        header_controls.append(ft.Row(row_items, alignment=ft.MainAxisAlignment.START))

    return ft.Container(
        ft.Column(
            header_controls + list(children),
            spacing=gap,
        ),
        width=width,
        padding=ft.padding.all(padding),
        bgcolor=bg,
        border_radius=THEME.R_XL,
        shadow=THEME.SHADOW_LIGHT if variant == "default" else THEME.SHADOW_SOFT,
        animate=ft.Animation(250, "ease"),
        on_hover=lambda e: setattr(
            e.control,
            "shadow",
            ft.BoxShadow(
                spread_radius=1,
                blur_radius=24,
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                offset=ft.Offset(0, 8),
            ),
        )
        if e.data == "true"
        else setattr(e.control, "shadow", THEME.SHADOW_LIGHT),
    )


# ============================================================
# KPI ROW
# ============================================================


def build_kpi_row(txs: list[dict]) -> ft.Control:
    total_income = sum(float(t["amount"]) for t in txs if float(t["amount"]) > 0)
    total_expense = sum(abs(float(t["amount"])) for t in txs if float(t["amount"]) < 0)
    net = total_income - total_expense
    avg_daily = 0.0
    if txs:
        unique_days = {t["date"] for t in txs}
        avg_daily = total_expense / max(1, len(unique_days))

    metrics = [
        ("Income", total_income, THEME.POSITIVE),
        ("Expense", total_expense, THEME.NEGATIVE),
        ("Net", net, THEME.POSITIVE if net >= 0 else THEME.NEGATIVE),
        ("Avg Daily Spend", avg_daily, THEME.WARNING),
        ("Transactions", len(txs), THEME.PURPLE),
    ]

    chips = []
    for label, value, color in metrics:
        chips.append(
            ft.Container(
                ft.Column(
                    [
                        ft.Text(label, size=11, color=THEME.TEXT_MUTED),
                        ft.Text(
                            fmt_number(value)
                            if isinstance(value, (int, float))
                            else str(value),
                            size=20,
                            weight=ft.FontWeight.W_700,
                            color=color,
                        ),
                    ],
                    spacing=2,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=14),
                bgcolor=THEME.SURFACE_SUBTLE,
                border_radius=THEME.R_LG,
            )
        )
    return ft.Row(chips, spacing=14, wrap=True)


# ============================================================
# ACCOUNTS SECTION
# ============================================================


def build_accounts_section(accounts) -> ft.Control:
    currency_totals = defaultdict(float)
    for acc in accounts:
        for b in acc.balances:
            currency_totals[b["currency"]] += float(b["balance"])

    total_row = ft.Row(
        [
            ft.Row(
                [
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text(cur, size=11, color=THEME.TEXT_MUTED),
                                ft.Text(
                                    fmt_number(amt),
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                    color=THEME.POSITIVE
                                    if amt >= 0
                                    else THEME.NEGATIVE,
                                ),
                            ],
                            spacing=2,
                        ),
                        padding=ft.padding.all(10),
                        bgcolor=THEME.SURFACE_SUBTLE,
                        border_radius=THEME.R_MD,
                        margin=ft.margin.only(right=8, bottom=8),
                    )
                    for cur, amt in currency_totals.items()
                ],
                wrap=True,
                spacing=4,
            )
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    acc_cards = []
    for i, acc in enumerate(accounts):
        color = THEME.CHART_COLORS[i % len(THEME.CHART_COLORS)]
        balances = ft.Column(
            [
                ft.Text(
                    f"{b['currency']}: {fmt_number(float(b['balance']))}",
                    size=12,
                    color=color if float(b["balance"]) >= 0 else THEME.NEGATIVE,
                    weight=ft.FontWeight.W_600,
                )
                for b in acc.balances
            ],
            spacing=3,
        )
        acc_cards.append(
            ft.Container(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    ft.Text(
                                        acc.name[:2].upper(),
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                        size=13,
                                    ),
                                    width=34,
                                    height=34,
                                    bgcolor=color,
                                    alignment=ft.alignment.center,
                                    border_radius=THEME.R_MD,
                                ),
                                ft.Text(
                                    acc.name,
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=THEME.TEXT,
                                ),
                            ],
                            spacing=10,
                        ),
                        balances,
                    ],
                    spacing=10,
                ),
                padding=ft.padding.all(14),
                bgcolor=THEME.SURFACE_SUBTLE,
                border_radius=THEME.R_LG,
                width=190,
                margin=ft.margin.only(right=14, bottom=14),
            )
        )

    return Card(
        ft.Column(
            [
                ft.Text(
                    "Portfolio Summary",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=THEME.TEXT,
                ),
                total_row,
                ft.Row(acc_cards, wrap=True, spacing=0),
            ],
            spacing=18,
        ),
        title="Accounts",
        icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
    )


# ============================================================
# CATEGORY BAR CHART
# ============================================================


def build_category_bar_chart(cat_amounts: dict[str, float]) -> ft.Control:
    if not cat_amounts:
        return Card(
            empty_state("Category Breakdown"),
            title="Category Breakdown",
            icon=ft.Icons.DONUT_SMALL,
        )

    # Sort by absolute amount
    cat_amounts = dict(
        sorted(cat_amounts.items(), key=lambda x: abs(x[1]), reverse=True)
    )
    max_amount = max([abs(v) for v in cat_amounts.values()]) or 1
    bar_h = 30
    gap = 18
    bar_x = 160
    usable_w = 360
    top_pad = 10

    shapes: list[cv.Shape] = []
    for idx, (cat, amt) in enumerate(cat_amounts.items()):
        y = top_pad + idx * (bar_h + gap)
        ratio = abs(amt) / max_amount
        bar_w = max(2, int(usable_w * ratio))
        color = THEME.CHART_COLORS[idx % len(THEME.CHART_COLORS)]
        # rail
        shapes.append(
            cv.Rect(
                x=bar_x,
                y=y,
                width=usable_w,
                height=bar_h,
                paint=ft.Paint(color=THEME.SURFACE_SUBTLE),
            )
        )
        # fill
        shapes.append(
            cv.Rect(
                x=bar_x,
                y=y,
                width=bar_w,
                height=bar_h,
                paint=ft.Paint(color=color),
            )
        )
        # name
        shapes.append(
            cv.Text(
                12,
                y + 8,
                cat,
                ft.TextStyle(size=13, weight=ft.FontWeight.W_600, color=THEME.TEXT),
            )
        )
        # value
        shapes.append(
            cv.Text(
                bar_x + bar_w + 12,
                y + 8,
                fmt_number(amt),
                ft.TextStyle(size=12, color=color, weight=ft.FontWeight.BOLD),
            )
        )

    canvas_h = max(120, top_pad + len(cat_amounts) * (bar_h + gap))
    canvas = cv.Canvas(width=560, height=canvas_h, shapes=shapes)

    total_abs = sum(abs(v) for v in cat_amounts.values()) or 1
    legend_items = list(cat_amounts.items())[:6]
    legend = ft.Column(
        [
            ft.Row(
                [
                    ft.Container(
                        width=10,
                        height=10,
                        bgcolor=THEME.CHART_COLORS[i % len(THEME.CHART_COLORS)],
                        border_radius=3,
                    ),
                    ft.Text(
                        f"{k}: {(abs(v) / total_abs) * 100:4.1f}%",
                        size=11,
                        color=THEME.TEXT_MUTED,
                    ),
                ],
                spacing=6,
            )
            for i, (k, v) in enumerate(legend_items)
        ],
        spacing=6,
    )

    return Card(
        ft.Row([canvas, legend], spacing=20, alignment=ft.MainAxisAlignment.START),
        title="Category Breakdown",
        icon=ft.Icons.DONUT_SMALL,
    )


# ============================================================
# INCOME vs EXPENSE LINE CHART
# ============================================================


def build_income_expense_line_chart(month_income, month_expense) -> ft.Control:
    width = 560
    height = 260
    ml, mb, mt, mr = 55, 42, 24, 20
    months = sorted(
        set([m for m, _ in month_income] + [m for m, _ in month_expense]),
        key=lambda m: datetime.strptime(m, "%Y-%m") if m != "0000-00" else datetime.min,
    )
    income_map = {m: v for m, v in month_income}
    expense_map = {m: v for m, v in month_expense}
    vals = list(income_map.values()) + list(expense_map.values())
    max_val = max(vals, default=0) or 1
    plot_w = width - ml - mr
    plot_h = height - mt - mb

    def x_pos(i):
        return ml + (
            plot_w // 2 if len(months) <= 1 else int(i * (plot_w / (len(months) - 1)))
        )

    def y_pos(val):
        r = val / max_val
        return mt + (plot_h - int(plot_h * r))

    shapes: list[cv.Shape] = []
    # grid
    steps = 5
    for i in range(steps + 1):
        val = max_val * i / steps
        y = y_pos(val)
        shapes.append(
            cv.Line(
                x1=ml, y1=y, x2=ml + plot_w, y2=y, paint=ft.Paint(color=THEME.BORDER)
            )
        )
        shapes.append(
            cv.Text(
                8,
                y - 8,
                f"{val:.0f}",
                ft.TextStyle(size=11, color=THEME.TEXT_MUTED),
            )
        )
    # axes
    shapes.append(
        cv.Line(
            x1=ml, y1=mt, x2=ml, y2=mt + plot_h, paint=ft.Paint(color=THEME.TEXT_MUTED)
        )
    )
    shapes.append(
        cv.Line(
            x1=ml,
            y1=mt + plot_h,
            x2=ml + plot_w,
            y2=mt + plot_h,
            paint=ft.Paint(color=THEME.TEXT_MUTED),
        )
    )
    for idx, m in enumerate(months):
        x = x_pos(idx)
        shapes.append(
            cv.Text(
                x - 26,
                mt + plot_h + 12,
                m,
                ft.TextStyle(size=10, color=THEME.TEXT_MUTED),
            )
        )

    def plot(data_map, color, lift=True):
        last = None
        for idx, m in enumerate(months):
            val = data_map.get(m, 0)
            x = x_pos(idx)
            y = y_pos(val)
            shapes.append(cv.Circle(x=x, y=y, radius=5, paint=ft.Paint(color=color)))
            if last:
                shapes.append(
                    cv.Line(
                        x1=last[0],
                        y1=last[1],
                        x2=x,
                        y2=y,
                        paint=ft.Paint(color=color, stroke_width=3),
                    )
                )
            shapes.append(
                cv.Text(
                    x - 16,
                    y - 26 if lift else y + 10,
                    f"{val:.0f}",
                    ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color=color),
                )
            )
            last = (x, y)

    plot(income_map, THEME.POSITIVE, lift=True)
    plot(expense_map, THEME.NEGATIVE, lift=False)

    # Legend
    lx, ly = ml, mt - 18
    for label, color in [("Income", THEME.POSITIVE), ("Expense", THEME.NEGATIVE)]:
        shapes.append(
            cv.Rect(x=lx, y=ly, width=18, height=10, paint=ft.Paint(color=color))
        )
        shapes.append(
            cv.Text(
                lx + 26,
                ly - 4,
                label,
                ft.TextStyle(size=12, color=THEME.TEXT),
            )
        )
        lx += 110

    canvas = cv.Canvas(width=width, height=height, shapes=shapes)
    return Card(canvas, title="Income vs Expense (Monthly)", icon=ft.Icons.SHOW_CHART)


# ============================================================
# DAILY SPEND SPARKLINE
# ============================================================


def build_daily_spend_sparkline(txs: list[dict], days: int = 14) -> ft.Control:
    if not txs:
        return Card(
            empty_state("Daily Spend"),
            title="Daily Spend (Last 14 days)",
            icon=ft.Icons.TIMELAPSE,
        )

    today = datetime.today().date()
    start = today - timedelta(days=days - 1)
    daily_exp = defaultdict(float)
    for t in txs:
        try:
            d = datetime.strptime(t["date"], "%Y-%m-%d").date()
        except Exception:
            continue
        if start <= d <= today:
            amt = float(t["amount"])
            if amt < 0:
                daily_exp[d] += abs(amt)
    ordered = [start + timedelta(days=i) for i in range(days)]
    vals = [daily_exp.get(d, 0.0) for d in ordered]
    max_val = max(vals) or 1

    width, height = 560, 140
    ml, mb, mt, mr = 8, 24, 14, 8
    pw = width - ml - mr
    ph = height - mt - mb

    def x_pos(i):
        return ml + (
            pw // 2 if len(ordered) <= 1 else int(i * (pw / (len(ordered) - 1)))
        )

    def y_pos(v):
        return mt + (ph - int(ph * (v / max_val)))

    shapes: list[cv.Shape] = []
    last = None
    for i, v in enumerate(vals):
        x = x_pos(i)
        y = y_pos(v)
        if last:
            shapes.append(
                cv.Line(
                    x1=last[0],
                    y1=last[1],
                    x2=x,
                    y2=y,
                    paint=ft.Paint(color=THEME.AMBER, stroke_width=2),
                )
            )
        shapes.append(cv.Circle(x=x, y=y, radius=3, paint=ft.Paint(color=THEME.AMBER)))
        last = (x, y)

    # baseline
    shapes.append(
        cv.Line(
            x1=ml,
            y1=mt + ph,
            x2=ml + pw,
            y2=mt + ph,
            paint=ft.Paint(color=THEME.BORDER),
        )
    )
    shapes.append(
        cv.Text(
            ml,
            mt - 6,
            f"Max: {fmt_number(max_val, 0)}",
            ft.TextStyle(size=10, color=THEME.AMBER),
        )
    )

    total7 = sum(vals[-7:])
    avg7 = total7 / 7 if days >= 7 else total7 / max(1, len(vals))

    footer = ft.Row(
        [
            ft.Text(
                f"7-day total: {fmt_number(total7)}", size=11, color=THEME.TEXT_MUTED
            ),
            ft.Text(f"7-day avg: {fmt_number(avg7)}", size=11, color=THEME.TEXT_MUTED),
        ],
        spacing=16,
    )

    canvas = cv.Canvas(width=width, height=height, shapes=shapes)
    return Card(
        ft.Column([canvas, footer], spacing=10),
        title=f"Daily Spend (Last {days} days)",
        icon=ft.Icons.TIMELAPSE,
    )


# ============================================================
# BUDGET UTILIZATION
# ============================================================


def build_budget_chart(budgets: list[dict], cat_dict: dict[int, str]) -> ft.Control:
    if not budgets:
        return Card(
            empty_state("Budgets"), title="Budget Utilization", icon=ft.Icons.DATA_USAGE
        )

    # Precompute spent (avoid duplicate DB calls inside loops for alert and canvas)
    spent_map = {}
    for b in budgets:
        spent_map[b["id"]] = get_category_spend(
            b["category_id"], b["start_date"], b["end_date"]
        )

    shapes: list[cv.Shape] = []
    bar_h = 22
    gap = 18
    bar_x = 200
    width_full = 320
    top = 10

    alerts = []
    for idx, b in enumerate(budgets):
        spent = spent_map[b["id"]]
        amount = b["amount"] or 0
        pct = min(spent / amount, 1.0) if amount > 0 else 0
        base_y = top + idx * (bar_h + gap)

        rail_color = THEME.SURFACE_SUBTLE
        shapes.append(
            cv.Rect(
                x=bar_x,
                y=base_y,
                width=width_full,
                height=bar_h,
                paint=ft.Paint(color=rail_color),
            )
        )
        if pct < 0.8:
            color = THEME.POSITIVE
        elif pct < 1:
            color = THEME.WARNING
        else:
            color = THEME.NEGATIVE
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
                base_y + 5,
                cat_dict.get(b["category_id"], "Other"),
                ft.TextStyle(size=13, weight=ft.FontWeight.W_600, color=THEME.TEXT),
            )
        )
        shapes.append(
            cv.Text(
                bar_x + 10,
                base_y + 4,
                f"{fmt_number(spent, 0)}/{fmt_number(amount, 0)}",
                ft.TextStyle(
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE if pct > 0.35 else color,
                ),
            )
        )
        shapes.append(
            cv.Text(
                bar_x + width_full + 14,
                base_y + 4,
                f"{int(pct * 100)}%",
                ft.TextStyle(size=11, weight=ft.FontWeight.W_600, color=color),
            )
        )
        if amount > 0:
            if pct >= 1:
                alerts.append(("Exceeded", b, color))
            elif pct >= 0.9:
                alerts.append(("Near Limit", b, color))

    canvas_h = max(120, top + len(budgets) * (bar_h + gap))
    canvas = cv.Canvas(width=560, height=canvas_h, shapes=shapes)

    alert_controls = []
    for label, b, color in alerts:
        spent = spent_map[b["id"]]
        alert_controls.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER, size=15, color=color),
                    ft.Text(
                        f"{label}: {cat_dict.get(b['category_id'], 'Other')} ({fmt_number(spent, 0)}/{fmt_number(b['amount'], 0)})",
                        size=11,
                        color=color,
                    ),
                ],
                spacing=6,
            )
        )

    return Card(
        ft.Column(
            [canvas] + (alert_controls if alert_controls else []),
            spacing=12,
        ),
        title="Budget Utilization",
        icon=ft.Icons.DATA_USAGE,
    )


# ============================================================
# RECENT TRANSACTIONS
# ============================================================


def build_recent_transactions(limit=8) -> ft.Control:
    recent = get_recent_transactions(limit)
    if not recent:
        return Card(
            empty_state("Recent Transactions"),
            title="Recent Transactions",
            icon=ft.Icons.LIST,
        )

    rows = []
    for r in recent:
        color = THEME.POSITIVE if r.amount > 0 else THEME.NEGATIVE
        rows.append(
            ft.Container(
                ft.Row(
                    [
                        ft.Text(r.date, width=90, size=11, color=THEME.TEXT_MUTED),
                        ft.Text(
                            f"{fmt_number(r.amount)} {r.currency}",
                            width=130,
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color=color,
                        ),
                        ft.Text(
                            getattr(r, "category_name", "Other"),
                            width=130,
                            size=12,
                            color=THEME.TEXT,
                        ),
                        ft.Text(
                            f"Acc {r.account_id}",
                            width=70,
                            size=11,
                            color=THEME.TEXT_MUTED,
                        ),
                    ],
                    spacing=14,
                ),
                padding=ft.padding.symmetric(vertical=6, horizontal=10),
                bgcolor=THEME.SURFACE_SUBTLE,
                border_radius=THEME.R_MD,
                margin=ft.margin.only(bottom=6),
            )
        )

    return Card(
        ft.Column(rows, spacing=4),
        title="Recent Transactions",
        icon=ft.Icons.LIST,
    )


# ============================================================
# DASHBOARD ASSEMBLY
# ============================================================


def build_dashboard_content(timeframe_code: str) -> ft.Control:
    accounts = get_accounts()
    txs_all = get_transactions_for_analytics()
    categories = get_categories()
    cat_map = {c["id"]: c["name"] for c in categories}
    filtered = filter_transactions_by_timeframe(txs_all, timeframe_code)

    # Category sums (filtered)
    cat_amounts = defaultdict(float)
    for t in filtered:
        cat_amounts[cat_map.get(t["category_id"], "Other")] += float(t["amount"])

    # Monthly series
    month_income = defaultdict(float)
    month_expense = defaultdict(float)
    for t in filtered:
        mk = month_key(t["date"])
        amt = float(t["amount"])
        if amt > 0:
            month_income[mk] += amt
        else:
            month_expense[mk] += abs(amt)

    income_series = sorted(month_income.items(), key=lambda x: x[0])
    expense_series = sorted(month_expense.items(), key=lambda x: x[0])

    budgets = get_budgets()

    # Sections
    kpi_row = build_kpi_row(filtered)
    accounts_section = build_accounts_section(accounts)
    category_chart = build_category_bar_chart(dict(cat_amounts))
    line_chart = build_income_expense_line_chart(income_series, expense_series)
    budget_chart = build_budget_chart(budgets, cat_map)
    sparkline = build_daily_spend_sparkline(filtered, 14)
    recent_section = build_recent_transactions()

    left_col = ft.Column(
        [
            accounts_section,
            Card(kpi_row, title="Key Metrics", icon=ft.Icons.INSIGHTS),
            category_chart,
            budget_chart,
        ],
        spacing=24,
        expand=1,
    )

    right_col = ft.Column(
        [
            line_chart,
            sparkline,
            recent_section,
        ],
        spacing=24,
        expand=1,
    )

    return ft.ResponsiveRow(
        [
            ft.Container(left_col, col={"xs": 12, "md": 6}),
            ft.Container(right_col, col={"xs": 12, "md": 6}),
        ],
        run_spacing=28,
    )


# ============================================================
# PAGE ENTRY
# ============================================================


def dashboard_page(page: ft.Page):
    page.bgcolor = THEME.BG
    page.padding = 0

    content_container = ft.Container(expand=True)
    timeframe_dropdown = ft.Dropdown(
        label="Timeframe",
        value="30D",
        width=190,
        options=[ft.dropdown.Option(k, text=v) for k, v in TIMEFRAME_OPTIONS],
    )

    # Initial render
    content_container.content = build_dashboard_content(timeframe_dropdown.value)

    # Header chips
    timestamp_chip = ft.Container(
        ft.Text(
            f"Data as of {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            size=11,
            color=THEME.TEXT_MUTED,
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        bgcolor=THEME.SURFACE_SUBTLE,
        border_radius=THEME.R_LG,
        margin=ft.margin.only(left=14),
    )

    timeframe_label_chip = ft.Container(
        ft.Text(
            next(lbl for k, lbl in TIMEFRAME_OPTIONS if k == timeframe_dropdown.value),
            size=11,
            color=THEME.ACCENT,
            weight=ft.FontWeight.W_600,
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=ft.Colors.with_opacity(0.15, THEME.ACCENT),
        border_radius=THEME.R_LG,
        margin=ft.margin.only(left=6),
    )

    def update_timeframe_label():
        timeframe_label_chip.content = ft.Text(
            next(lbl for k, lbl in TIMEFRAME_OPTIONS if k == timeframe_dropdown.value),
            size=11,
            color=THEME.ACCENT,
            weight=ft.FontWeight.W_600,
        )

    def timeframe_changed(e):
        # Loading placeholder
        content_container.content = ft.Container(
            ft.Row(
                [
                    ft.ProgressRing(color=THEME.ACCENT),
                    ft.Text("Updating...", color=THEME.TEXT_MUTED),
                ],
                spacing=14,
            ),
            padding=ft.padding.all(30),
            alignment=ft.alignment.center,
        )
        content_container.update()

        # Rebuild content
        content_container.content = build_dashboard_content(timeframe_dropdown.value)
        update_timeframe_label()
        # Refresh timestamp
        timestamp_chip.content = ft.Text(
            f"Data as of {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            size=11,
            color=THEME.TEXT_MUTED,
        )
        content_container.update()

    timeframe_dropdown.on_change = timeframe_changed

    header_bar = ft.Row(
        [
            ft.Text(
                "Dashboard",
                size=32,
                weight=ft.FontWeight.W_700,
                color=THEME.ACCENT_ALT,
            ),
            timeframe_dropdown,
            timeframe_label_chip,
            timestamp_chip,
            ft.Container(expand=True),
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    scroll_view = ft.ListView(
        expand=True,
        spacing=28,
        padding=ft.padding.only(top=4),
        controls=[
            header_bar,
            ft.Divider(height=1, color=THEME.BORDER),
            content_container,
        ],
    )

    root = ft.Container(
        scroll_view,
        padding=ft.padding.symmetric(horizontal=28, vertical=12),
        bgcolor=THEME.BG,
        expand=True,
    )
    return root
