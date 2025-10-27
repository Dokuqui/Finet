import datetime
import sqlite3
from typing import Optional, Dict, Any, List

from .connection import get_db_connection
from .transactions import add_transaction
from app.db.accounts import increment_account_balance
from app.db.categories import get_categories

FREQUENCIES = {"daily", "weekly", "monthly", "yearly", "custom_interval", "once"}

ADJUST_BALANCES = True


def _category_map() -> Dict[int, str]:
    try:
        return {c["id"]: c["name"] for c in get_categories()}
    except Exception:
        return {}


def _today() -> datetime.date:
    return datetime.date.today()


def _parse(date_str: str) -> datetime.date:
    return datetime.date.fromisoformat(date_str)


def _fmt(d: datetime.date) -> str:
    return d.isoformat()


def create_recurring(
    account_id: int,
    category_id: int,
    amount: float,
    currency: str,
    frequency: str,
    start_date: str,
    end_date: Optional[str],
    notes: str = "",
    interval: Optional[int] = None,
    day_of_month: Optional[int] = None,
    weekday: Optional[int] = None,
    active: bool = True,
) -> int:
    """
    amount MUST already be signed (positive income, negative expense).
    """
    if frequency not in FREQUENCIES:
        raise ValueError(f"Unsupported frequency: {frequency}")

    start = _parse(start_date)
    if end_date:
        _parse(end_date)

    if frequency == "once":
        end_date = _fmt(start)

    now_iso = datetime.datetime.utcnow().isoformat()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO recurring_transactions
        (account_id, category_id, amount, currency, frequency, interval,
         day_of_month, weekday, start_date, end_date, next_occurrence,
         last_generated_at, notes, active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            account_id,
            category_id,
            amount,
            currency,
            frequency,
            interval,
            day_of_month,
            weekday,
            _fmt(start),
            end_date,
            _fmt(start),
            None,
            notes,
            1 if active else 0,
            now_iso,
            now_iso,
        ),
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid


def list_recurring(active_only: bool = True) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if active_only:
        rows = conn.execute(
            "SELECT * FROM recurring_transactions WHERE active=1 ORDER BY next_occurrence ASC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM recurring_transactions ORDER BY active DESC, next_occurrence ASC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_upcoming_recurring(
    limit: int = 5, days_ahead: int = 30
) -> List[Dict[str, Any]]:
    """
    Get upcoming active recurring transactions within the next X days.
    """
    today = _today()
    end_date = today + datetime.timedelta(days=days_ahead)

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            r.*,
            c.name as category_name,
            c.icon as category_icon,
            c.type as category_type
        FROM recurring_transactions r
        LEFT JOIN categories c ON r.category_id = c.id
        WHERE
            r.active = 1
            AND r.next_occurrence <= ?
        ORDER BY r.next_occurrence ASC
        LIMIT ?
        """,
        (_fmt(end_date), limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recurring(recurring_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM recurring_transactions WHERE id=?", (recurring_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_recurring(recurring_id: int, **fields):
    if not fields:
        return
    allowed = {
        "amount",
        "currency",
        "frequency",
        "interval",
        "day_of_month",
        "weekday",
        "start_date",
        "end_date",
        "notes",
        "active",
        "next_occurrence",
        "last_generated_at",
    }
    setters = []
    values = []
    for k, v in fields.items():
        if k in allowed:
            setters.append(f"{k}=?")
            values.append(v)
    if not setters:
        return
    values.append(datetime.datetime.utcnow().isoformat())
    values.append(recurring_id)
    conn = get_db_connection()
    conn.execute(
        f"UPDATE recurring_transactions SET {', '.join(setters)}, updated_at=? WHERE id=?",
        values,
    )
    conn.commit()
    conn.close()


def deactivate_recurring(recurring_id: int):
    update_recurring(recurring_id, active=0)


def _compute_next(
    rec: Dict[str, Any], from_date: datetime.date
) -> Optional[datetime.date]:
    freq = rec.get("frequency")
    if not freq:
        return None

    if freq == "once":
        return None

    end_date = rec.get("end_date")
    end_dt = _parse(end_date) if end_date else None

    try:
        current = _parse(rec["next_occurrence"])
    except Exception:
        return None

    if current < from_date:
        current = from_date

    def end_check(candidate: datetime.date):
        if end_dt and candidate > end_dt:
            return None
        return candidate

    interval = rec.get("interval") or 1

    if freq == "daily":
        return end_check(current + datetime.timedelta(days=1))
    if freq == "weekly":
        return end_check(current + datetime.timedelta(weeks=interval))
    if freq == "custom_interval":
        return end_check(current + datetime.timedelta(days=interval))
    if freq == "monthly":
        base = current
        year = base.year + (base.month - 1 + interval) // 12
        month = (base.month - 1 + interval) % 12 + 1
        day = rec.get("day_of_month") or base.day
        for _ in range(6):
            try:
                cand = datetime.date(year, month, day)
                break
            except ValueError:
                day -= 1
        else:
            return None
        return end_check(cand)
    if freq == "yearly":
        try:
            cand = datetime.date(current.year + interval, current.month, current.day)
        except ValueError:
            if current.month == 2 and current.day == 29:
                cand = datetime.date(current.year + interval, 2, 28)
            else:
                return None
        return end_check(cand)
    return None


def generate_due_transactions(today: Optional[datetime.date] = None) -> int:
    """
    Generates all occurrences whose next_occurrence <= today.
    Inserts signed amounts and optionally updates balances.
    """
    if today is None:
        today = _today()

    recs = list_recurring(active_only=True)
    if not recs:
        return 0

    cat_map = _category_map()
    generated = 0

    for rec in recs:
        if "next_occurrence" not in rec or not rec["next_occurrence"]:
            if rec.get("start_date"):
                update_recurring(rec["id"], next_occurrence=rec["start_date"])
                rec["next_occurrence"] = rec["start_date"]
            else:
                continue

        try:
            next_occ = _parse(rec["next_occurrence"])
        except Exception:
            continue

        while rec.get("active") and next_occ <= today:
            try:
                add_transaction(
                    date=_fmt(next_occ),
                    amount=rec["amount"],  # already signed
                    category_id=rec["category_id"],
                    account_id=rec["account_id"],
                    notes=rec.get("notes") or "",
                    currency=rec["currency"],
                    recurring_id=rec["id"],
                    occurrence_date=_fmt(next_occ),
                )
                generated += 1

                if ADJUST_BALANCES:
                    increment_account_balance(
                        rec["account_id"], rec["currency"], rec["amount"]
                    )
            except sqlite3.IntegrityError:
                pass

            new_next = _compute_next(rec, next_occ)
            if not new_next:
                update_recurring(
                    rec["id"],
                    active=0,
                    last_generated_at=datetime.datetime.utcnow().isoformat(),
                )
                rec["active"] = 0
                break
            update_recurring(
                rec["id"],
                next_occurrence=_fmt(new_next),
                last_generated_at=datetime.datetime.utcnow().isoformat(),
            )
            rec["next_occurrence"] = _fmt(new_next)
            next_occ = new_next

    return generated
