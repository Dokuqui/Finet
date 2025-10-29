import os
import sys
import flet as ft
from app.startup import initialize
from app.ui.dashboard import dashboard_page

from app.ui.transactions import (
    transactions_page,
    _handle_file_picker_result,
    export_to_csv,
    import_from_csv,
)
from app.ui.accounts import accounts_page
from app.ui.budgets import budgets_page
from app.ui.settings import settings_page


def main(page: ft.Page):
    db_name = "finet.db"

    base_dir = getattr(page, "app_directory", None) or os.getcwd()

    assets_dir = os.path.join(base_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    db_path = os.path.join(assets_dir, db_name)

    print(f"[Main] Using database path: {db_path}")

    initialize(db_path)
    page.title = "Finet - Personal Finance Tracker"
    page.bgcolor = ft.Colors.GREY_50

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def notify_main(msg: str, color=ft.Colors.BLUE_400, duration=3000):
        sb = ft.SnackBar(ft.Text(msg), bgcolor=color, duration=duration)
        page.snack_bar = sb
        sb.open = True
        page.update()

    file_picker.on_result = lambda e: _handle_file_picker_result(
        e, page, notify_main, export_to_csv, import_from_csv
    )

    tab_content_generators = [
        dashboard_page,
        lambda p: transactions_page(p, file_picker),
        accounts_page,
        budgets_page,
        settings_page,
    ]

    def on_tab_change(e):
        idx = tabs.selected_index
        
        tabs_to_refresh = [1, 2] 

        if tabs.tabs[idx].content is None or idx in tabs_to_refresh:
            print(f"[Tabs] Regenerating content for tab index {idx}")
            tabs.tabs[idx].content = tab_content_generators[idx](page)
        
        page.update()

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Dashboard"),
            ft.Tab(text="Transactions", content=None),
            ft.Tab(text="Accounts", content=None),
            ft.Tab(text="Budgets", content=None),
            ft.Tab(text="Settings", content=None),
        ],
        indicator_color=ft.Colors.BLUE_400,
        label_color=ft.Colors.GREY_900,
        unselected_label_color=ft.Colors.GREY_500,
        scrollable=False,
        expand=True,
        on_change=on_tab_change,
    )

    tabs.tabs[0].content = tab_content_generators[0](page)

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
    view = ft.FLET_APP

    args = sys.argv[1:]
    if "--web" in args or os.getenv("FLET_VIEW") == "web":
        view = ft.WEB_BROWSER
    elif "--headless" in args:
        view = None

    ft.app(target=main, view=view, port=8550)
