import flet as ft
from app.db import get_recent_transactions

def dashboard_page(page: ft.Page):
    transactions = get_recent_transactions(5)
    return ft.Column([
        ft.Text("Dashboard"),
        ft.Text("Recent Transactions:"),
        *[ft.Text(f"{tx['date']} | {tx['amount']} | {tx['category']} | {tx['account']}") for tx in transactions]
    ])