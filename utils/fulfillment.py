"""
Fulfillment / order helper functions.
"""

from utils.db import run_query, run_execute
from utils.priority import compute_priority_score, risk_band, current_time
from datetime import datetime


# ---------- Status flow ----------
STATUS_FLOW = [
    "NEW", "PROCESSING", "READY_TO_PICK", "PICKING",
    "PACKED", "STAGED", "SHIPPED", "DELIVERED",
]

EXCEPTION_STATUSES = [
    "ON_HOLD", "STOCK_ISSUE", "PICKING_ISSUE", "PACKING_ISSUE", "COURIER_DELAY",
]


def next_status(current: str) -> str | None:
    """Return the next status in the normal flow, or None."""
    if current in EXCEPTION_STATUSES:
        return None
    try:
        idx = STATUS_FLOW.index(current)
        return STATUS_FLOW[idx + 1] if idx + 1 < len(STATUS_FLOW) else None
    except ValueError:
        return None


def timestamp_col_for_status(status: str) -> str | None:
    """Return the timestamp column name for a status."""
    mapping = {
        "NEW": "created_at",
        "PROCESSING": "processing_at",
        "READY_TO_PICK": "ready_to_pick_at",
        "PICKING": "picking_at",
        "PACKED": "packed_at",
        "STAGED": "staged_at",
        "SHIPPED": "shipped_at",
        "DELIVERED": "delivered_at",
    }
    return mapping.get(status)


# ---------- Queries ----------

def get_today_summary() -> dict:
    """Dashboard-level counts for today."""
    today = current_time().strftime("%Y-%m-%d")
    rows = run_query(
        "SELECT status, priority, COUNT(*) AS cnt "
        "FROM orders WHERE order_date = ? GROUP BY status, priority",
        (today,),
    )

    summary = {
        "total": 0,
        "priority_orders": 0,
        "by_status": {},
        "new": 0,
        "processing": 0,
        "ready_to_pick": 0,
        "picking": 0,
        "packed": 0,
        "staged": 0,
        "shipped": 0,
        "delivered": 0,
        "stock_issues": 0,
        "on_hold": 0,
        "picking_issues": 0,
        "packing_issues": 0,
        "courier_delays": 0,
    }
    for r in rows:
        summary["total"] += r["cnt"]
        summary["by_status"][r["status"]] = summary["by_status"].get(r["status"], 0) + r["cnt"]
        if r["priority"] == "High":
            summary["priority_orders"] += r["cnt"]
        key = r["status"].lower()
        if key in summary:
            summary[key] += r["cnt"]

    # Open exceptions
    exc = run_query(
        "SELECT COUNT(*) AS cnt FROM exceptions WHERE status IN ('Open','Investigating')"
    )
    summary["open_exceptions"] = exc[0]["cnt"] if exc else 0

    return summary


def get_orders_needing_attention(limit: int = 20) -> list[dict]:
    """Orders that need immediate action — scored and ranked."""
    today = current_time().strftime("%Y-%m-%d")
    sql = """
    SELECT
        o.order_id, o.customer_name, o.channel, o.priority,
        o.ship_by, o.status, o.assigned_picker,
        c.pickup_time AS courier_pickup,
        (SELECT COUNT(*) FROM exceptions e
         WHERE e.order_id = o.order_id AND e.status IN ('Open','Investigating')) AS exc_count
    FROM orders o
    LEFT JOIN couriers c ON o.courier_id = c.courier_id
    WHERE o.order_date = ?
      AND o.status NOT IN ('DELIVERED', 'CANCELLED', 'SHIPPED')
    """
    orders = run_query(sql, (today,))

    for o in orders:
        score = compute_priority_score(
            o["priority"], o["ship_by"], o["status"],
            o["exc_count"] > 0, o.get("courier_pickup"),
        )
        o["score"] = score
        o["risk"] = risk_band(score)

    orders.sort(key=lambda x: x["score"], reverse=True)
    return orders[:limit]


def get_filtered_orders(
    status_filter: str | None = None,
    priority_filter: str | None = None,
    risk_filter: str | None = None,
    search: str | None = None,
    today_only: bool = True,
) -> list[dict]:
    """Filtered order list with priority scores."""
    today = current_time().strftime("%Y-%m-%d")
    conditions = []
    params: list = []

    if today_only:
        conditions.append("o.order_date = ?")
        params.append(today)
    if status_filter and status_filter != "All":
        conditions.append("o.status = ?")
        params.append(status_filter)
    if priority_filter and priority_filter != "All":
        conditions.append("o.priority = ?")
        params.append(priority_filter)
    if search:
        conditions.append("(o.order_id LIKE ? OR o.customer_name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = f"""
    SELECT
        o.order_id, o.customer_name, o.channel, o.priority,
        o.order_date, o.order_time, o.ship_by, o.status,
        o.assigned_picker, o.warehouse,
        c.courier_name, c.pickup_time AS courier_pickup,
        (SELECT COUNT(*) FROM exceptions e
         WHERE e.order_id = o.order_id AND e.status IN ('Open','Investigating')) AS exc_count
    FROM orders o
    LEFT JOIN couriers c ON o.courier_id = c.courier_id
    {where}
    ORDER BY o.order_id DESC
    """
    orders = run_query(sql, tuple(params))

    for o in orders:
        score = compute_priority_score(
            o["priority"], o["ship_by"], o["status"],
            o["exc_count"] > 0, o.get("courier_pickup"),
        )
        o["score"] = score
        o["risk"] = risk_band(score)

    if risk_filter and risk_filter != "All":
        orders = [o for o in orders if o["risk"] == risk_filter]

    return orders


def get_order_detail(order_id: str) -> dict | None:
    """Full order detail including items, courier, and exceptions."""
    rows = run_query(
        """SELECT o.*, c.courier_name, c.pickup_time AS courier_pickup,
                  c.cost_per_order AS courier_cost, c.delivery_days
           FROM orders o
           LEFT JOIN couriers c ON o.courier_id = c.courier_id
           WHERE o.order_id = ?""",
        (order_id,),
    )
    if not rows:
        return None
    order = rows[0]

    # Items
    order["items"] = run_query(
        """SELECT oi.*, p.product_name, p.variant, p.category,
                  COALESCE(inv.location_code, '') AS location_code,
                  COALESCE(inv.quantity, 0) - COALESCE(inv.reserved, 0) AS available_stock
           FROM order_items oi
           JOIN products p ON oi.sku = p.sku
           LEFT JOIN inventory inv ON oi.sku = inv.sku AND inv.warehouse = 'Main'
           WHERE oi.order_id = ?""",
        (order_id,),
    )

    # Exceptions
    order["exceptions"] = run_query(
        "SELECT * FROM exceptions WHERE order_id = ? ORDER BY created_at DESC",
        (order_id,),
    )

    # Score
    has_exc = any(e["status"] in ("Open", "Investigating") for e in order["exceptions"])
    order["score"] = compute_priority_score(
        order["priority"], order["ship_by"], order["status"],
        has_exc, order.get("courier_pickup"),
    )
    order["risk"] = risk_band(order["score"])

    return order


def update_order_status(order_id: str, new_status: str) -> None:
    """Update order status and record timestamp."""
    ts_col = timestamp_col_for_status(new_status)
    now_iso = current_time().isoformat()
    if ts_col:
        run_execute(
            f"UPDATE orders SET status = ?, {ts_col} = ? WHERE order_id = ?",
            (new_status, now_iso, order_id),
        )
    else:
        run_execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (new_status, order_id),
        )
    # Log event
    run_execute(
        "INSERT INTO fulfillment_events (order_id, event_type, event_detail) "
        "VALUES (?, ?, ?)",
        (order_id, "STATUS_CHANGE", f"Status changed to {new_status}"),
    )


def get_picking_queue() -> list[dict]:
    """Orders ready to pick or currently being picked."""
    today = current_time().strftime("%Y-%m-%d")
    sql = """
    SELECT o.order_id, o.customer_name, o.priority, o.ship_by,
           o.status, o.assigned_picker,
           COUNT(oi.item_id) AS item_count
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_date = ?
      AND o.status IN ('READY_TO_PICK', 'PICKING')
    GROUP BY o.order_id
    ORDER BY
        CASE o.priority WHEN 'High' THEN 0 ELSE 1 END,
        o.ship_by
    """
    return run_query(sql, (today,))


def confirm_pick(order_id: str, sku: str, picked_sku: str) -> str:
    """Confirm a pick: returns 'CONFIRMED' or 'MISMATCH'."""
    status = "CONFIRMED" if sku == picked_sku else "MISMATCH"
    run_execute(
        "UPDATE order_items SET picked_sku = ?, pick_status = ? "
        "WHERE order_id = ? AND sku = ?",
        (picked_sku, status, order_id, sku),
    )
    if status == "MISMATCH":
        # Auto-create exception
        exc_count = run_query(
            "SELECT COUNT(*) AS cnt FROM exceptions", ()
        )[0]["cnt"]
        run_execute(
            "INSERT INTO exceptions (exception_id, order_id, exception_type, "
            "priority, status, owner, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"EX{exc_count + 1:04d}", order_id, "WRONG_SKU", "High", "Open",
             "Picker", f"Expected {sku}, picked {picked_sku}"),
        )
        run_execute(
            "UPDATE orders SET status = 'PICKING_ISSUE' WHERE order_id = ?",
            (order_id,),
        )
    return status
