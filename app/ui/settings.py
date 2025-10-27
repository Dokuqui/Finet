import os
import datetime
import threading
import traceback
import flet as ft

from app.utils.backup import backup_db, restore_db
from app.db.connection import DB_PATH  # <-- FIX: Import the correct DB path


def _default_backup_name() -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"./backups/finet-backup-{ts}.db"


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

    # Basic filepicker support (guarded)
    file_picker = None
    use_file_picker = hasattr(ft, "FilePicker")
    if use_file_picker:

        def _on_filepicker_result(e):
            try:
                if getattr(e, "files", None):
                    # choose first file path for restore
                    restore_in.value = e.files[0].path
                elif getattr(e, "path", None):
                    backup_out.value = e.path
            except Exception:
                pass
            if hasattr(page, "call_from_thread"):
                page.call_from_thread(lambda: page.update())
            else:
                page.update()

        try:
            file_picker = ft.FilePicker(on_result=_on_filepicker_result)
            if file_picker not in page.overlay:
                page.overlay.append(file_picker)
        except Exception:
            file_picker = None
            use_file_picker = False

    # Safe notify implemented to be callable from worker threads
    def notify(msg: str, color: str | None = None):
        def _do():
            sb = ft.SnackBar(
                ft.Text(msg, color=ft.Colors.WHITE), bgcolor=color or ft.Colors.GREY_800
            )
            page.snack_bar = sb
            sb.open = True
            page.update()

        if hasattr(page, "call_from_thread"):
            page.call_from_thread(_do)
        else:
            _do()

    encrypt_chk.on_change = lambda e: (
        setattr(passphrase, "visible", encrypt_chk.value),
        setattr(passphrase_confirm, "visible", encrypt_chk.value),
        page.update(),
    )

    def _run_in_thread(target, *args, **kwargs):
        t = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        t.start()
        return t

    # Worker with robust logging + UI callbacks via page.call_from_thread
    def _create_backup_worker(db_path: str, out_path: str, passph: str | None):
        log_path = os.path.join("app", "utils", "backup-debug.log")
        try:
            if hasattr(page, "call_from_thread"):
                page.call_from_thread(
                    lambda: setattr(progress, "visible", True) or page.update()
                )
            else:
                progress.visible = True
                page.update()

            # actual backup
            backup_db(db_path, out_path, passphrase=passph, overwrite=True)

            notify(f"Backup created: {out_path}", ft.Colors.BLUE_400)

        except Exception as ex:
            # write traceback to debug log
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
            if hasattr(page, "call_from_thread"):
                page.call_from_thread(
                    lambda: setattr(progress, "visible", False) or page.update()
                )
            else:
                progress.visible = False
                page.update()

    def _restore_backup_worker(in_path: str, db_path: str, passph: str | None):
        log_path = os.path.join("app", "utils", "backup-debug.log")
        try:
            if hasattr(page, "call_from_thread"):
                page.call_from_thread(
                    lambda: setattr(progress, "visible", True) or page.update()
                )
            else:
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
            if hasattr(page, "call_from_thread"):
                page.call_from_thread(
                    lambda: setattr(progress, "visible", False) or page.update()
                )
            else:
                progress.visible = False
                page.update()

    # Event handlers that give immediate feedback (so clicks always produce visible result)
    def on_backup_click(e):
        # immediate feedback so user knows UI responded
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
                out_path = out_path + ".enc"
        else:
            passph = None

        out_dir = os.path.dirname(out_path) or "."
        os.makedirs(out_dir, exist_ok=True)

        db_path = DB_PATH  # <-- FIX: Use the imported DB_PATH
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
        db_path = DB_PATH  # <-- FIX: Use the imported DB_PATH
        notify("Starting restore...", ft.Colors.GREY_700)
        _run_in_thread(_restore_backup_worker, in_path, db_path, passph)

    backup_btn.on_click = on_backup_click
    restore_btn.on_click = on_restore_click

    # optional browse buttons if file picker available
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

    page_controls = ft.Column([backup_card, restore_card], spacing=16)

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
