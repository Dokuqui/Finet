import os
import shutil
import tempfile
import argparse
from typing import Optional

from .crypto import encrypt_file, decrypt_file, is_encrypted_file

"""
Utilities to backup and restore the local database file.

Usage examples (CLI):
    python -m app.utils.backup backup --db-path ./data/finet.db --out ./backups/backup.db
    python -m app.utils.backup backup --db-path ./data/finet.db --out ./backups/backup.db.enc --passphrase "s3cret"

    python -m app.utils.backup restore --in ./backups/backup.db --db-path ./data/finet.db
    python -m app.utils.backup restore --in ./backups/backup.db.enc --db-path ./data/finet.db --passphrase "s3cret"
"""


def backup_db(
    db_path: str,
    out_path: str,
    passphrase: Optional[str] = None,
    overwrite: bool = False,
):
    """
    Create a backup of db_path at out_path. If passphrase is provided, the output will be encrypted.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file does not exist: {db_path}")
    if os.path.exists(out_path) and not overwrite:
        raise FileExistsError(
            f"Output path exists: {out_path} (set overwrite=True to replace)"
        )

    if passphrase:
        # write a temp copy and encrypt that into out_path
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tmp_path = tf.name
        try:
            shutil.copy2(db_path, tmp_path)
            encrypt_file(tmp_path, out_path, passphrase)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    else:
        shutil.copy2(db_path, out_path)


def restore_db(
    in_path: str, db_path: str, passphrase: Optional[str] = None, overwrite: bool = True
):
    """
    Restore a backup file (optionally encrypted) into db_path.
    If encrypted, pass the passphrase used during backup.
    """
    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Backup file does not exist: {in_path}")
    if os.path.exists(db_path) and not overwrite:
        raise FileExistsError(
            f"Database already exists at {db_path} (set overwrite=True to replace)"
        )

    if passphrase:
        # decrypt into a temporary file then move into place
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tmp_path = tf.name
        try:
            decrypt_file(in_path, tmp_path, passphrase)
            shutil.move(tmp_path, db_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    else:
        # If input is encrypted but passphrase is not supplied, try to detect and error
        if is_encrypted_file(in_path):
            raise ValueError("Input appears encrypted but no passphrase provided.")
        shutil.copy2(in_path, db_path)


# CLI
def _cli():
    parser = argparse.ArgumentParser(
        prog="finet-backup", description="Backup / restore Finet DB"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_backup = sub.add_parser("backup", help="Create a backup")
    p_backup.add_argument("--db-path", required=True)
    p_backup.add_argument("--out", required=True)
    p_backup.add_argument("--passphrase", required=False, default=None)
    p_backup.add_argument("--overwrite", action="store_true")

    p_restore = sub.add_parser("restore", help="Restore from a backup")
    p_restore.add_argument("--in", dest="in_path", required=True)
    p_restore.add_argument("--db-path", required=True)
    p_restore.add_argument("--passphrase", required=False, default=None)
    p_restore.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()
    if args.cmd == "backup":
        backup_db(args.db_path, args.out, args.passphrase, overwrite=args.overwrite)
        print("Backup created:", args.out)
    elif args.cmd == "restore":
        restore_db(
            args.in_path, args.db_path, args.passphrase, overwrite=args.overwrite
        )
        print("Restore complete:", args.db_path)


if __name__ == "__main__":
    _cli()
