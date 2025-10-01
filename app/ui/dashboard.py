import flet as ft
from app.db.transactions import get_recent_transactions
from app.db.accounts import get_accounts

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
                            f"{b['currency']}: {b['balance']:.2f}",
                            style="bodyMedium",
                            color=ft.Colors.BLUE_400 if float(b["balance"]) >= 0 else ft.Colors.RED_400,
                        )
                        for b in acc.balances
                    ],
                ],
                spacing=4,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            padding=ft.padding.all(14),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.GREY_200,
                offset=ft.Offset(0, 2),
            ),
            width=190,
            margin=ft.margin.only(right=18, bottom=12),
        )
        for acc in accounts
    ]

    balances_row = ft.Row(
        balances_cards,
        alignment=ft.MainAxisAlignment.START,
        spacing=0,
        wrap=True,
    )

    transactions = get_recent_transactions(5)
    recent_tx_controls = [
        ft.Container(
            ft.Row(
                [
                    ft.Text(tx.date, style="bodyMedium", color=ft.Colors.GREY_700, width=90),
                    ft.Text(f"{tx.amount:.2f} {tx.currency}", style="bodyMedium", color=ft.Colors.BLUE_400 if tx.amount > 0 else ft.Colors.RED_400, width=100),
                    ft.Text(getattr(tx, "category_name", "Other"), style="bodyMedium", width=110),
                    ft.Text(f"Account: {tx.account_id}", style="bodyMedium", color=ft.Colors.GREY_600, width=120),
                ],
                spacing=18,
            ),
            padding=ft.padding.only(top=8, bottom=8),
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            margin=ft.margin.only(bottom=6),
        )
        for tx in transactions
    ] if transactions else [
        ft.Container(
            ft.Text(
                "No transactions found. Add your first transaction above!",
                italic=True,
                color=ft.Colors.GREY_600,
            ),
            padding=16,
            bgcolor=ft.Colors.GREY_100,
            border_radius=10,
            alignment=ft.alignment.center,
            margin=ft.margin.only(top=8, bottom=8),
        )
    ]

    main_card = ft.Container(
        ft.Column(
            [
                ft.Text(
                    "Dashboard",
                    style="headlineSmall",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                ft.Divider(height=2, color=ft.Colors.GREY_100),
                ft.Text(
                    "Account Balances:",
                    style="titleMedium",
                    color=ft.Colors.GREY_800,
                    weight=ft.FontWeight.BOLD,
                ),
                balances_row,
                ft.Divider(height=2, color=ft.Colors.GREY_100),
                ft.Text(
                    "Recent Transactions:",
                    style="headlineSmall",
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                ft.Column(recent_tx_controls, spacing=0),
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
        width=750,
    )

    return ft.Container(
        content=ft.Column(
            [main_card],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll="auto",
        ),
        expand=True,
        alignment=ft.alignment.top_center,
        bgcolor=ft.Colors.GREY_50,
    )