import flet as ft
from app.ui.dashboard import dashboard_page
from app.ui.transactions import transactions_page
from app.db import init_db

def accounts():
    return ft.Text("Accounts Page")

def budgets():
    return ft.Text("Budgets Page")

def main(page: ft.Page):
    init_db()
    page.title = "Finet - Personal Finance Tracker"
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Dashboard", content=dashboard_page(page)),
            ft.Tab(text="Transactions", content=transactions_page(page)),
            ft.Tab(text="Accounts", content=accounts()),
            ft.Tab(text="Budgets", content=budgets()),
        ],
        indicator_color=ft.Colors.BLUE_400,
        label_color=ft.Colors.BLACK,
        unselected_label_color=ft.Colors.GREY_500,
        scrollable=False,
        expand=True,
    )
    page.add(tabs)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)