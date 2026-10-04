"""
Priority scoring engine.

Score formula:
  Priority order          +30
  Deadline < 2 hours      +30
  Deadline < 4 hours      +15
  Stock issue              +25
  Active exception         +20
  Courier pickup < 1 hr   +15

Risk bands:
  >= 60  → URGENT   (🔴)
  40–59  → AT RISK  (🟠)
  < 40   → ON TRACK (🟢)
"""

from datetime import datetime, timedelta

def current_time() -> datetime:
    """Return the actual current time."""
    return datetime.now()


def compute_priority_score(
    priority: str,
    ship_by: str | None,
    status: str,
    has_exception: bool,
    courier_pickup_time: str | None = None,
) -> int:
    """Return an integer priority score (higher = more urgent)."""
    score = 0
    now = current_time()

    # 1. Priority order
    if priority == "High":
        score += 30

    # 2. Deadline proximity
    if ship_by:
        try:
            deadline = datetime.fromisoformat(ship_by)
            remaining = deadline - now
            if remaining < timedelta(0):
                score += 40  # SLA breached
            elif remaining < timedelta(hours=2):
                score += 30
            elif remaining < timedelta(hours=4):
                score += 15
        except (ValueError, TypeError):
            pass

    # 3. Status-based risk
    if status in ("STOCK_ISSUE", "ON_HOLD"):
        score += 25
    elif status in ("PICKING_ISSUE", "PACKING_ISSUE"):
        score += 20
    elif status == "COURIER_DELAY":
        score += 15

    # 4. Active exception
    if has_exception:
        score += 20

    # 5. Courier pickup approaching
    if courier_pickup_time and status in ("PACKED", "STAGED"):
        try:
            pickup_h, pickup_m = map(int, courier_pickup_time.split(":"))
            pickup_dt = now.replace(hour=pickup_h, minute=pickup_m, second=0)
            if (pickup_dt - now) < timedelta(hours=1):
                score += 15
        except (ValueError, TypeError):
            pass

    return score


def risk_band(score: int) -> str:
    """Return the risk label for a priority score."""
    if score >= 60:
        return "URGENT"
    elif score >= 40:
        return "AT RISK"
    return "ON TRACK"


def risk_emoji(band: str) -> str:
    return {"URGENT": "🔴", "AT RISK": "🟠", "ON TRACK": "🟢"}.get(band, "⚪")


def deadline_display(ship_by: str | None) -> str:
    """Human-friendly remaining-time string."""
    if not ship_by:
        return "—"
    now = current_time()
    try:
        deadline = datetime.fromisoformat(ship_by)
    except (ValueError, TypeError):
        return "—"
    diff = deadline - now
    if diff < timedelta(0):
        return "❌ SLA BREACHED"
    total_min = int(diff.total_seconds() // 60)
    if total_min < 60:
        return f"🔴 {total_min} min remaining"
    hours = total_min // 60
    mins = total_min % 60
    if hours < 4:
        return f"🟠 {hours}h {mins}m remaining"
    if hours < 24:
        return f"🟢 {hours}h remaining"
    days = hours // 24
    return f"🟢 {days} day{'s' if days > 1 else ''}"
