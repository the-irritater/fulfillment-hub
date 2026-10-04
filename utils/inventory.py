"""
Inventory helper functions.
"""

from utils.db import run_query, run_execute


def get_inventory_summary() -> list[dict]:
    """Full inventory view with availability calculation."""
    sql = """
    SELECT
        p.sku,
        p.product_name,
        p.variant,
        p.category,
        COALESCE(main.quantity, 0)     AS main_wh,
        COALESCE(main.reserved, 0)     AS reserved,
        COALESCE(main.location_code, '') AS main_location,
        COALESCE(sec.quantity, 0)       AS secondary_wh,
        COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) AS available,
        CASE
            WHEN COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) <= 0
                 AND COALESCE(sec.quantity, 0) > 0
            THEN 'TRANSFER'
            WHEN COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) <= 0
            THEN 'OUT_OF_STOCK'
            WHEN COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) <= 5
            THEN 'LOW'
            ELSE 'OK'
        END AS stock_status
    FROM products p
    LEFT JOIN inventory main ON p.sku = main.sku AND main.warehouse = 'Main'
    LEFT JOIN inventory sec  ON p.sku = sec.sku  AND sec.warehouse = 'Secondary'
    ORDER BY
        CASE
            WHEN COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) <= 0
                 AND COALESCE(sec.quantity, 0) > 0 THEN 0
            WHEN COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) <= 0 THEN 1
            WHEN COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) <= 5 THEN 2
            ELSE 3
        END,
        p.sku
    """
    return run_query(sql)


def check_stock_for_order(order_id: str) -> list[dict]:
    """Check stock availability for every item in an order."""
    sql = """
    SELECT
        oi.sku,
        p.product_name,
        p.variant,
        oi.quantity AS required_qty,
        COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) AS available,
        COALESCE(sec.quantity, 0) AS secondary_available,
        COALESCE(main.location_code, '') AS location_code,
        CASE
            WHEN COALESCE(main.quantity, 0) - COALESCE(main.reserved, 0) >= oi.quantity THEN 'OK'
            WHEN COALESCE(sec.quantity, 0) >= oi.quantity THEN 'TRANSFER_NEEDED'
            ELSE 'INSUFFICIENT'
        END AS availability
    FROM order_items oi
    JOIN products p ON oi.sku = p.sku
    LEFT JOIN inventory main ON oi.sku = main.sku AND main.warehouse = 'Main'
    LEFT JOIN inventory sec  ON oi.sku = sec.sku  AND sec.warehouse = 'Secondary'
    WHERE oi.order_id = ?
    """
    return run_query(sql, (order_id,))


def create_transfer(sku: str, quantity: int,
                    from_warehouse: str = "Secondary",
                    to_warehouse: str = "Main") -> None:
    """Create an inventory transfer request."""
    run_execute(
        "INSERT INTO transfers (sku, from_warehouse, to_warehouse, quantity) "
        "VALUES (?, ?, ?, ?)",
        (sku, from_warehouse, to_warehouse, quantity),
    )


def get_pending_transfers() -> list[dict]:
    """Return pending / in-transit transfers."""
    sql = """
    SELECT t.*, p.product_name, p.variant
    FROM transfers t
    JOIN products p ON t.sku = p.sku
    WHERE t.status IN ('REQUESTED', 'IN_TRANSIT')
    ORDER BY t.requested_at DESC
    """
    return run_query(sql)
