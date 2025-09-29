import flet as ft

def dashboard():
    return ft.Text("Dashboard Page")

def transactions():
    return ft.Text("Transactions Page")

def accounts():
    return ft.Text("Accounts Page")

def budgets():
    return ft.Text("Budgets Page")

def main(page: ft.Page):
    page.title = "Finet - Personal Finance Tracker"
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Dashboard", content=dashboard()),
            ft.Tab(text="Transactions", content=transactions()),
            ft.Tab(text="Accounts", content=accounts()),
            ft.Tab(text="Budgets", content=budgets()),
        ]
    )
    page.add(tabs)

if __name__ == "__main__":
    ft.app(target=main)