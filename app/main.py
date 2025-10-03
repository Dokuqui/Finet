import flet as ft
from app.startup import initialize
from app.ui.dashboard import dashboard_page
from app.ui.transactions import transactions_page
from app.ui.accounts import accounts_page
from app.ui.budgets import budgets_page


def main(page: ft.Page):
    initialize()
    page.title = "Finet - Personal Finance Tracker"
    page.bgcolor = ft.Colors.GREY_50

    tab_contents = [dashboard_page, transactions_page, accounts_page, budgets_page]

    def on_tab_change(e):
        idx = tabs.selected_index
        tabs.tabs[idx].content = tab_contents[idx](page)
        page.update()

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Dashboard", content=dashboard_page(page)),
            ft.Tab(text="Transactions", content=transactions_page(page)),
            ft.Tab(text="Accounts", content=accounts_page(page)),
            ft.Tab(text="Budgets", content=budgets_page(page)),
        ],
        indicator_color=ft.Colors.BLUE_400,
        label_color=ft.Colors.GREY_900,
        unselected_label_color=ft.Colors.GREY_500,
        scrollable=False,
        expand=True,
        on_change=on_tab_change,
    )

    header = ft.Container(
        ft.Text(
            "Finet",
            style="headlineMedium",
            weight=ft.FontWeight.BOLD,
            size=30,
            color=ft.Colors.BLUE_400,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=10, bottom=10),
    )

    page.add(
        ft.Column(
            [
                header,
                ft.Divider(height=2, color=ft.Colors.GREY_100),
                tabs,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            spacing=0,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
