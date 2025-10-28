import os
import datetime
import threading
import traceback
import flet as ft
from decimal import Decimal, InvalidOperation

from app.utils.backup import backup_db, restore_db
from app.db.connection import DB_PATH
from app.db import settings as db_settings
from app.services.converter import ALL_CURRENCIES, get_currency_symbol
from app.services.api import fetch_latest_rates
from app.utils.recalculate import recalculate_all_conversions


def _default_backup_name() -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"./backups/finet-backup-{ts}.db"


# ========== Currency Settings UI ==========
def build_currency_settings_card(page: ft.Page) -> ft.Control:
    def snack(msg: str, color=ft.Colors.GREEN_400, duration=3000):
        if not page:
            return
        sb = ft.SnackBar(ft.Text(msg), bgcolor=color, duration=duration)
        page.snack_bar = sb
        sb.open = True
        page.update()

    try:
        current_base = db_settings.get_base_currency()
        all_rates = db_settings.get_exchange_rates()
    except Exception as e:
        return ft.Container(
            ft.Text(f"Error loading currency settings: {e}", color=ft.Colors.RED_400),
            padding=20,
        )

    progress_ring = ft.ProgressRing(visible=False, width=16, height=16)

    base_currency_dd = ft.Dropdown(
        label="Base Currency for Analytics",
        value=current_base,
        options=[ft.dropdown.Option(c) for c in ALL_CURRENCIES],
        width=300,
    )

    rate_fields = {}
    rates_column = ft.Column(spacing=8)

    def build_rate_fields(base_code: str):
        rates_column.controls.clear()
        rate_fields.clear()
        base_sym = get_currency_symbol(base_code)
        for code in ALL_CURRENCIES:
            if code == base_code:
                continue
            rate = all_rates.get(code, 1.0)
            field = ft.TextField(
                label=f"1 {base_sym} = ... {code}",
                value=f"{rate:.4f}",
                width=250,
                keyboard_type=ft.KeyboardType.NUMBER,
            )
            rate_fields[code] = field
            rates_column.controls.append(field)
        if rates_column.page:
            rates_column.update()

    def on_base_change(e):
        new_base = base_currency_dd.value
        all_rates[new_base] = 1.0
        build_rate_fields(new_base)
        on_fetch_rates(e)

    base_currency_dd.on_change = on_base_change

    def save_rates(e):
        try:
            new_base = base_currency_dd.value
            db_settings.set_base_currency(new_base)
            new_rates = {}
            for code, field in rate_fields.items():
                try:
                    new_rates[code] = float(Decimal(field.value))
                except (InvalidOperation, ValueError):
                    snack(f"Invalid rate for {code}, skipping.", ft.Colors.RED_400)
                    return
            new_rates[new_base] = 1.0
            db_settings.set_exchange_rates(new_rates)
            from app.services import converter

            converter.get_base_currency.cache_clear()
            converter.get_conversion_rates.cache_clear()
            snack("Currency settings saved!")
        except Exception as ex:
            snack(f"Error saving: {ex}", ft.Colors.RED_400)

    def _fetch_rates_worker():
        base = base_currency_dd.value

        progress_ring.visible = True
        page.update()

        fetched = fetch_latest_rates(base)

        if fetched:
            for code, field in rate_fields.items():
                if code in fetched:
                    field.value = f"{fetched[code]:.4f}"
            all_rates.update(fetched)
            rates_column.update()
            snack(f"Fetched latest rates for {base}.")
        else:
            snack(f"Failed to fetch rates.", ft.Colors.RED_400)

        progress_ring.visible = False
        page.update()

    def on_fetch_rates(e):
        threading.Thread(target=_fetch_rates_worker, daemon=True).start()

    def _recalculate_worker():
        progress_ring.visible = True
        page.update()
        snack(
            "Recalculating all historical data... This may take a moment.",
            ft.Colors.BLUE_400,
            duration=5000,
        )

        try:
            tx_count, rec_count = recalculate_all_conversions()
            snack(
                f"Recalculated {tx_count} transactions and {rec_count} recurring items."
            )
        except Exception as ex:
            snack(f"Error recalculating: {ex}", ft.Colors.RED_400, duration=5000)
        finally:
            progress_ring.visible = False
            page.update()

    def on_recalculate(e):
        save_rates(e)
        threading.Thread(target=_recalculate_worker, daemon=True).start()

    save_btn = ft.ElevatedButton(
        "Save Rates",
        icon=ft.Icons.SAVE,
        on_click=save_rates,
        bgcolor=ft.Colors.BLUE_400,
    )
    fetch_btn = ft.OutlinedButton(
        "Fetch Latest",
        icon=ft.Icons.DOWNLOAD,
        on_click=on_fetch_rates,
        tooltip="Fetch latest rates",
    )
    recalc_btn = ft.TextButton(
        "Recalculate Historical Data",
        icon=ft.Icons.CALCULATE_OUTLINED,
        on_click=on_recalculate,
        tooltip="Update past data with saved rates",
    )

    build_rate_fields(current_base)

    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Currency Settings", size=16, weight=ft.FontWeight.BOLD
                        ),
                        progress_ring,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(
                    "Set your main currency and exchange rates (relative to base).",
                    size=12,
                    color=ft.Colors.GREY_600,
                ),
                base_currency_dd,
                rates_column,
                ft.Row(
                    [fetch_btn, ft.Container(expand=True), save_btn],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Divider(),
                ft.Row([recalc_btn], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=12,
        ),
        padding=ft.padding.all(18),
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=12,
            color=ft.Colors.GREY_100,
            offset=ft.Offset(0, 6),
        ),
    )


# ========== Main Settings Page Function ==========


def settings_page(page: ft.Page) -> ft.Control:
    progress = ft.ProgressRing(visible=False)

    backup_out = ft.TextField(
        label="Backup output path", value=_default_backup_name(), width=520
    )
    encrypt_chk = ft.Checkbox(label="Encrypt backup (passphrase)", value=False)
    passphrase = ft.TextField(
        label="Passphrase",
        password=True,
        can_reveal_password=True,
        width=320,
        visible=False,
    )
    passphrase_confirm = ft.TextField(
        label="Confirm passphrase",
        password=True,
        can_reveal_password=True,
        width=320,
        visible=False,
    )
    backup_btn = ft.ElevatedButton(
        "Create Backup", icon=ft.Icons.BACKUP, bgcolor=ft.Colors.BLUE_400
    )
    restore_in = ft.TextField(label="Backup file to restore (path)", width=520)
    restore_passphrase = ft.TextField(
        label="Passphrase (if encrypted)",
        password=True,
        can_reveal_password=True,
        width=320,
    )
    restore_btn = ft.ElevatedButton(
        "Restore Backup", icon=ft.Icons.UPLOAD_FILE, bgcolor=ft.Colors.GREEN_400
    )

    file_picker = None
    use_file_picker = hasattr(ft, "FilePicker")
    if use_file_picker:

        def _on_filepicker_result(e):
            try:
                if getattr(e, "files", None):
                    restore_in.value = e.files[0].path
                elif getattr(e, "path", None):
                    backup_out.value = e.path
            except Exception:
                pass
            page.update()

        try:
            file_picker = ft.FilePicker(on_result=_on_filepicker_result)
            if file_picker not in page.overlay:
                page.overlay.append(file_picker)
        except Exception:
            file_picker = None
            use_file_picker = False

    def notify(msg: str, color: str | None = None, duration=3000):
        sb = ft.SnackBar(
            ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=color or ft.Colors.GREY_800,
            duration=duration,
        )
        page.snack_bar = sb
        sb.open = True
        page.update()

    encrypt_chk.on_change = lambda e: (
        setattr(passphrase, "visible", encrypt_chk.value),
        setattr(passphrase_confirm, "visible", encrypt_chk.value),
        page.update(),
    )

    def _run_in_thread(target, *args, **kwargs):
        t = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        t.start()
        return t

    def _create_backup_worker(db_path: str, out_path: str, passph: str | None):
        log_path = os.path.join("app", "utils", "backup-debug.log")
        try:
            progress.visible = True
            page.update()

            backup_db(db_path, out_path, passphrase=passph, overwrite=True)
            notify(f"Backup created: {out_path}", ft.Colors.BLUE_400)
        except Exception as ex:
            try:
                with open(log_path, "a", encoding="utf-8") as lf:
                    lf.write(
                        f"\n[{datetime.datetime.now().isoformat()}] Backup exception:\n"
                    )
                    lf.write(traceback.format_exc())
            except Exception:
                pass
            notify(f"Backup failed: {ex}", ft.Colors.RED_400)
        finally:
            progress.visible = False
            page.update()

    def _restore_backup_worker(in_path: str, db_path: str, passph: str | None):
        log_path = os.path.join("app", "utils", "backup-debug.log")
        try:
            progress.visible = True
            page.update()

            restore_db(in_path, db_path, passphrase=passph, overwrite=True)
            notify(f"Restore completed to: {db_path}", ft.Colors.GREEN_400)
        except Exception as ex:
            try:
                with open(log_path, "a", encoding="utf-8") as lf:
                    lf.write(
                        f"\n[{datetime.datetime.now().isoformat()}] Restore exception:\n"
                    )
                    lf.write(traceback.format_exc())
            except Exception:
                pass
            notify(f"Restore failed: {ex}", ft.Colors.RED_400)
        finally:
            progress.visible = False
            page.update()

    def on_backup_click(e):
        notify("Starting backup...", ft.Colors.GREY_700)
        out_path = backup_out.value.strip() or _default_backup_name()
        if encrypt_chk.value:
            pw = passphrase.value or ""
            pw2 = passphrase_confirm.value or ""
            if not pw:
                notify("Enter passphrase for encryption", ft.Colors.RED_400)
                return
            if pw != pw2:
                notify("Passphrase confirmation does not match", ft.Colors.RED_400)
                return
            passph = pw
            if not out_path.endswith(".enc"):
                out_path += ".enc"
        else:
            passph = None
        out_dir = os.path.dirname(out_path) or "."
        os.makedirs(out_dir, exist_ok=True)
        db_path = DB_PATH
        if not os.path.exists(db_path):
            notify(f"Database not found at {db_path}", ft.Colors.RED_400)
            return
        _run_in_thread(_create_backup_worker, db_path, out_path, passph)

    def on_restore_click(e):
        in_path = restore_in.value.strip()
        if not in_path:
            notify("Provide path to backup file", ft.Colors.RED_400)
            return
        if not os.path.exists(in_path):
            notify("Backup file does not exist", ft.Colors.RED_400)
            return
        passph = restore_passphrase.value.strip() or None
        db_path = DB_PATH
        notify("Starting restore...", ft.Colors.GREY_700)
        _run_in_thread(_restore_backup_worker, in_path, db_path, passph)

    backup_btn.on_click = on_backup_click
    restore_btn.on_click = on_restore_click

    browse_buttons = []
    if use_file_picker and file_picker is not None:

        def on_pick_backup(e):
            try:
                file_picker.save_file(suggested_name=os.path.basename(backup_out.value))
            except Exception:
                try:
                    file_picker.pick_files(allow_multiple=False)
                except Exception:
                    notify("File picker not available", ft.Colors.ORANGE_400)

        def on_pick_restore(e):
            try:
                file_picker.pick_files(allow_multiple=False)
            except Exception:
                notify("File picker not available", ft.Colors.ORANGE_400)

        browse_backup_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN, tooltip="Browse", on_click=on_pick_backup
        )
        browse_restore_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN, tooltip="Browse", on_click=on_pick_restore
        )
        browse_buttons = [browse_backup_btn, browse_restore_btn]

    currency_card = build_currency_settings_card(page)
    backup_card = ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Create Backup", size=16, weight=ft.FontWeight.BOLD),
                        progress,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [backup_out] + ([browse_buttons[0]] if browse_buttons else []),
                    spacing=12,
                ),
                ft.Row([encrypt_chk, passphrase, passphrase_confirm], spacing=12),
                ft.Row([backup_btn], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=12,
        ),
        padding=ft.padding.all(18),
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=12,
            color=ft.Colors.GREY_100,
            offset=ft.Offset(0, 6),
        ),
    )
    restore_card = ft.Container(
        ft.Column(
            [
                ft.Text("Restore Backup", size=16, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [restore_in] + ([browse_buttons[1]] if browse_buttons else []),
                    spacing=12,
                ),
                ft.Row([restore_passphrase], spacing=12),
                ft.Row([restore_btn], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=12,
        ),
        padding=ft.padding.all(18),
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=12,
            color=ft.Colors.GREY_100,
            offset=ft.Offset(0, 6),
        ),
    )

    page_controls = ft.Column(
        [currency_card, backup_card, restore_card],
        spacing=16,
        scroll="auto",
        expand=True,
    )

    return ft.Container(
        ft.Column(
            [
                ft.Text(
                    "Settings",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                ft.Divider(),
                page_controls,
            ],
            spacing=18,
        ),
        padding=ft.padding.all(24),
        expand=True,
        bgcolor=ft.Colors.GREY_50,
    )
