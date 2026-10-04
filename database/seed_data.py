"""
Seed data generator for Fulfillment Hub.
Creates ~1500 realistic orders, 80 products, inventory, couriers, and exceptions.
Intentionally injects operational problems (stock issues, SLA breaches, wrong SKUs, etc.)
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "fulfillment.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

random.seed(42)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

CATEGORIES = {
    "T-Shirts": [
        ("Classic T-Shirt", ["Black/S", "Black/M", "Black/L", "Black/XL",
                             "White/S", "White/M", "White/L", "White/XL",
                             "Navy/M", "Navy/L", "Grey/M", "Grey/L"]),
        ("Premium Polo", ["Black/M", "Black/L", "White/M", "White/L",
                          "Navy/M", "Navy/L"]),
        ("V-Neck Tee", ["Black/M", "Black/L", "White/M", "White/L"]),
    ],
    "Shoes": [
        ("Running Shoes", ["White/7", "White/8", "White/9", "White/10",
                           "Black/8", "Black/9", "Black/10"]),
        ("Casual Sneakers", ["Grey/8", "Grey/9", "Grey/10",
                             "White/8", "White/9"]),
    ],
    "Bags": [
        ("Laptop Bag", ["Black", "Navy", "Grey"]),
        ("Backpack", ["Black", "Blue", "Red"]),
        ("Tote Bag", ["Canvas", "Black", "White"]),
    ],
    "Accessories": [
        ("Water Bottle", ["500ml", "750ml", "1L"]),
        ("Sunglasses", ["Black", "Brown", "Tortoise"]),
        ("Cap", ["Black", "White", "Navy", "Red"]),
        ("Belt", ["Black/S", "Black/M", "Black/L", "Brown/M", "Brown/L"]),
        ("Wallet", ["Black", "Brown", "Tan"]),
    ],
    "Electronics": [
        ("Wireless Earbuds", ["Black", "White"]),
        ("Phone Case", ["Clear", "Black", "Blue"]),
        ("Power Bank", ["10000mAh", "20000mAh"]),
    ],
}

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Ananya", "Diya", "Saanvi", "Aanya", "Aadhya", "Isha",
    "Priya", "Meera", "Neha", "Kavya", "Rohan", "Karan", "Vikram", "Rahul",
    "Amit", "Sneha", "Pooja", "Riya", "Nisha", "Tanvi", "Harsh", "Dev",
    "Manish", "Suresh", "Rajesh", "Deepa", "Swati", "Anjali", "Shreya", "Ankita",
]
LAST_NAMES = [
    "Sharma", "Patel", "Gupta", "Singh", "Kumar", "Verma", "Joshi", "Mehta",
    "Reddy", "Nair", "Iyer", "Rao", "Das", "Mishra", "Chopra", "Malhotra",
    "Bhat", "Kapoor", "Banerjee", "Mukherjee", "Shah", "Desai", "Pillai",
    "Agarwal", "Saxena", "Thakur", "Kulkarni", "Jain", "Pandey", "Tiwari",
]

CHANNELS = ["Amazon", "Flipkart", "Website", "Wholesale", "Walk-in"]
CHANNEL_WEIGHTS = [35, 30, 20, 10, 5]

PICKERS = ["Ramu", "Sunil", "Anil", "Manoj", "Ganesh", "Dinesh", "Rajendra", "Suresh"]

COURIERS_DATA = [
    ("COU-A", "BlueDart",    65, "16:00", 2, "9876543210"),
    ("COU-B", "DTDC",        80, "17:00", 1, "9876543211"),
    ("COU-C", "Delhivery",   55, "15:00", 3, "9876543212"),
    ("COU-D", "Ecom Express", 70, "16:30", 2, "9876543213"),
    ("COU-E", "India Post",  40, "14:00", 5, "9876543214"),
]

STATUS_FLOW = [
    "NEW", "PROCESSING", "READY_TO_PICK", "PICKING",
    "PACKED", "STAGED", "SHIPPED", "DELIVERED",
]

EXCEPTION_STATUSES = ["ON_HOLD", "STOCK_ISSUE", "PICKING_ISSUE", "PACKING_ISSUE", "COURIER_DELAY"]

LOCATION_AISLES = ["A", "B", "C", "D", "E"]


def _sku(product_name: str, variant: str) -> str:
    """Generate a deterministic SKU string."""
    abbr = {
        "Classic T-Shirt": "TSH",
        "Premium Polo": "POL",
        "V-Neck Tee": "VNK",
        "Running Shoes": "RSH",
        "Casual Sneakers": "CSN",
        "Laptop Bag": "LBG",
        "Backpack": "BPK",
        "Tote Bag": "TBG",
        "Water Bottle": "BOT",
        "Sunglasses": "SNG",
        "Cap": "CAP",
        "Belt": "BLT",
        "Wallet": "WLT",
        "Wireless Earbuds": "EBD",
        "Phone Case": "PHC",
        "Power Bank": "PWB",
    }
    prefix = abbr.get(product_name, product_name[:3].upper())
    suffix = variant.replace("/", "-").replace(" ", "").upper()
    return f"{prefix}-{suffix}"


def _rand_location(warehouse: str) -> str:
    """Random shelf location code like A-03-12."""
    aisle = random.choice(LOCATION_AISLES)
    shelf = random.randint(1, 8)
    slot = random.randint(1, 20)
    return f"{aisle}-{shelf:02d}-{slot:02d}"


def seed():
    """Main seeder — drops existing DB and creates fresh data."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create schema
    with open(SCHEMA_PATH) as f:
        cur.executescript(f.read())

    # ------------------------------------------------------------------
    # 1. Products
    # ------------------------------------------------------------------
    products = []
    pid = 1
    for category, items in CATEGORIES.items():
        for product_name, variants in items:
            for variant in variants:
                sku = _sku(product_name, variant)
                products.append((f"P{pid:03d}", sku, product_name, variant, category,
                                 round(random.uniform(0.1, 3.0), 2)))
                pid += 1

    cur.executemany(
        "INSERT INTO products (product_id, sku, product_name, variant, category, weight_kg) "
        "VALUES (?, ?, ?, ?, ?, ?)", products
    )
    all_skus = [p[1] for p in products]

    # ------------------------------------------------------------------
    # 2. Inventory
    # ------------------------------------------------------------------
    inventory_rows = []
    for sku in all_skus:
        main_qty = random.choices(
            [0, random.randint(1, 5), random.randint(6, 40)],
            weights=[8, 20, 72], k=1
        )[0]
        sec_qty = random.randint(5, 30)
        reserved = min(main_qty, random.randint(0, max(1, main_qty // 2)))
        inventory_rows.append((sku, "Main", main_qty, reserved,
                               _rand_location("Main")))
        inventory_rows.append((sku, "Secondary", sec_qty, 0,
                               _rand_location("Secondary")))

    cur.executemany(
        "INSERT INTO inventory (sku, warehouse, quantity, reserved, location_code) "
        "VALUES (?, ?, ?, ?, ?)", inventory_rows
    )

    # ------------------------------------------------------------------
    # 3. Couriers
    # ------------------------------------------------------------------
    for c in COURIERS_DATA:
        cur.execute(
            "INSERT INTO couriers (courier_id, courier_name, cost_per_order, "
            "pickup_time, delivery_days, contact_phone) VALUES (?, ?, ?, ?, ?, ?)", c
        )

    # ------------------------------------------------------------------
    # 4. Orders — ~1500 total, ~250 are "today"
    # ------------------------------------------------------------------
    today = datetime.now()
    orders = []
    order_items_rows = []
    fulfillment_events = []
    exceptions_rows = []

    oid = 1
    exc_id = 1

    # -- historical orders (past 30 days)
    for day_offset in range(30, 0, -1):
        day = today - timedelta(days=day_offset)
        n_orders = random.randint(30, 55)
        for _ in range(n_orders):
            order_id = f"ORD{oid:04d}"
            oid += 1
            customer = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
            priority = random.choices(["High", "Normal"], weights=[15, 85], k=1)[0]
            hour = random.randint(7, 18)
            minute = random.randint(0, 59)
            order_time = f"{hour:02d}:{minute:02d}"
            order_date = day.strftime("%Y-%m-%d")

            if priority == "High":
                ship_by = (day + timedelta(hours=random.choice([4, 6, 8]))).isoformat()
            else:
                ship_by = (day + timedelta(days=1)).isoformat()

            # Historical orders are all delivered
            status = "DELIVERED"
            courier = random.choice(COURIERS_DATA)
            picker = random.choice(PICKERS)

            orders.append((
                order_id, customer, channel, priority, order_date, order_time,
                ship_by, status, "Main", courier[0],
                f"TRK{random.randint(100000, 999999)}", picker,
                day.isoformat(),
                (day + timedelta(minutes=10)).isoformat(),
                (day + timedelta(minutes=30)).isoformat(),
                (day + timedelta(minutes=50)).isoformat(),
                (day + timedelta(hours=1)).isoformat(),
                (day + timedelta(hours=2)).isoformat(),
                (day + timedelta(hours=3)).isoformat(),
                (day + timedelta(days=courier[4])).isoformat(),
                None,
            ))

            # Add 1-4 items per order
            n_items = random.choices([1, 2, 3, 4], weights=[30, 40, 20, 10], k=1)[0]
            chosen_skus = random.sample(all_skus, min(n_items, len(all_skus)))
            for sk in chosen_skus:
                qty = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
                order_items_rows.append((order_id, sk, qty, sk, "CONFIRMED"))

    # -- Today's orders (~250)
    today_order_count = 250
    for i in range(today_order_count):
        order_id = f"ORD{oid:04d}"
        oid += 1
        customer = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
        priority = random.choices(["High", "Normal"], weights=[18, 82], k=1)[0]
        hour = random.randint(7, 14)
        minute = random.randint(0, 59)
        order_time = f"{hour:02d}:{minute:02d}"
        order_date = today.strftime("%Y-%m-%d")

        if priority == "High":
            ship_by_dt = today.replace(hour=random.choice([14, 15, 16, 17]))
        else:
            ship_by_dt = today + timedelta(days=1)
        ship_by = ship_by_dt.isoformat()

        # Distribute today's orders across statuses
        bucket = random.random()
        if bucket < 0.04:
            status = "NEW"
            ts = _status_timestamps(today, status, hour, minute)
        elif bucket < 0.12:
            status = "PROCESSING"
            ts = _status_timestamps(today, status, hour, minute)
        elif bucket < 0.18:
            status = "READY_TO_PICK"
            ts = _status_timestamps(today, status, hour, minute)
        elif bucket < 0.30:
            status = "PICKING"
            ts = _status_timestamps(today, status, hour, minute)
        elif bucket < 0.46:
            status = "PACKED"
            ts = _status_timestamps(today, status, hour, minute)
        elif bucket < 0.58:
            status = "STAGED"
            ts = _status_timestamps(today, status, hour, minute)
        elif bucket < 0.72:
            status = "SHIPPED"
            ts = _status_timestamps(today, status, hour, minute)
        elif bucket < 0.82:
            status = "DELIVERED"
            ts = _status_timestamps(today, status, hour, minute)
        elif bucket < 0.87:
            status = "STOCK_ISSUE"
            ts = _status_timestamps(today, "PROCESSING", hour, minute)
        elif bucket < 0.91:
            status = "PICKING_ISSUE"
            ts = _status_timestamps(today, "PICKING", hour, minute)
        elif bucket < 0.94:
            status = "COURIER_DELAY"
            ts = _status_timestamps(today, "STAGED", hour, minute)
        elif bucket < 0.97:
            status = "ON_HOLD"
            ts = _status_timestamps(today, "PROCESSING", hour, minute)
        else:
            status = "PACKING_ISSUE"
            ts = _status_timestamps(today, "PICKING", hour, minute)

        courier = random.choice(COURIERS_DATA)
        picker = random.choice(PICKERS) if status not in ("NEW", "PROCESSING") else None
        tracking = f"TRK{random.randint(100000, 999999)}" if status in ("SHIPPED", "DELIVERED") else None

        orders.append((
            order_id, customer, channel, priority, order_date, order_time,
            ship_by, status, "Main", courier[0], tracking, picker,
            ts["created_at"], ts["processing_at"], ts["ready_to_pick_at"],
            ts["picking_at"], ts["packed_at"], ts["staged_at"],
            ts["shipped_at"], ts["delivered_at"], None,
        ))

        # Add 1-4 items per order
        n_items = random.choices([1, 2, 3, 4], weights=[30, 40, 20, 10], k=1)[0]
        chosen_skus = random.sample(all_skus, min(n_items, len(all_skus)))
        for sk in chosen_skus:
            qty = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
            if status == "PICKING_ISSUE" and random.random() < 0.5:
                # Simulate wrong SKU picked
                wrong_sku = random.choice([s for s in all_skus if s != sk])
                order_items_rows.append((order_id, sk, qty, wrong_sku, "MISMATCH"))
            elif status in ("SHIPPED", "DELIVERED", "PACKED", "STAGED"):
                order_items_rows.append((order_id, sk, qty, sk, "CONFIRMED"))
            else:
                order_items_rows.append((order_id, sk, qty, None, "PENDING"))

        # Generate exceptions for problem statuses
        if status == "STOCK_ISSUE":
            exceptions_rows.append((
                f"EX{exc_id:04d}", order_id, "STOCK_SHORTAGE", "High", "Open",
                "Warehouse", f"Insufficient stock in main warehouse for order {order_id}",
                None, today.isoformat(), None
            ))
            exc_id += 1
        elif status == "PICKING_ISSUE":
            exceptions_rows.append((
                f"EX{exc_id:04d}", order_id, "WRONG_SKU", "High", "Open",
                random.choice(PICKERS), f"SKU mismatch detected during picking for {order_id}",
                None, today.isoformat(), None
            ))
            exc_id += 1
        elif status == "COURIER_DELAY":
            exceptions_rows.append((
                f"EX{exc_id:04d}", order_id, "COURIER_MISSED_PICKUP", "High", "Open",
                "Logistics", f"Courier missed scheduled pickup for {order_id}",
                None, today.isoformat(), None
            ))
            exc_id += 1
        elif status == "PACKING_ISSUE":
            exceptions_rows.append((
                f"EX{exc_id:04d}", order_id, "BOX_MISPLACED", "Medium", "Investigating",
                "Warehouse", f"Packed box misplaced in staging area for {order_id}",
                None, today.isoformat(), None
            ))
            exc_id += 1

    # Add some resolved historical exceptions for realism
    for _ in range(30):
        exc_type = random.choice(["STOCK_SHORTAGE", "WRONG_SKU", "BOX_MISPLACED",
                                  "COURIER_MISSED_PICKUP", "DAMAGED_ITEM"])
        hist_order = f"ORD{random.randint(1, oid - 250):04d}"
        resolved_day = today - timedelta(days=random.randint(1, 20))
        exceptions_rows.append((
            f"EX{exc_id:04d}", hist_order, exc_type,
            random.choice(["High", "Medium"]), "Resolved",
            random.choice(PICKERS + ["Warehouse", "Logistics"]),
            f"Historical exception for {hist_order}",
            f"Resolved by {random.choice(PICKERS)}",
            (resolved_day - timedelta(hours=random.randint(1, 8))).isoformat(),
            resolved_day.isoformat(),
        ))
        exc_id += 1

    # ------------------------------------------------------------------
    # Bulk insert
    # ------------------------------------------------------------------
    cur.executemany(
        "INSERT INTO orders (order_id, customer_name, channel, priority, order_date, "
        "order_time, ship_by, status, warehouse, courier_id, tracking_number, "
        "assigned_picker, created_at, processing_at, ready_to_pick_at, picking_at, "
        "packed_at, staged_at, shipped_at, delivered_at, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        orders,
    )

    cur.executemany(
        "INSERT INTO order_items (order_id, sku, quantity, picked_sku, pick_status) "
        "VALUES (?, ?, ?, ?, ?)", order_items_rows,
    )

    cur.executemany(
        "INSERT INTO exceptions (exception_id, order_id, exception_type, priority, "
        "status, owner, description, resolution, created_at, resolved_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", exceptions_rows,
    )

    conn.commit()
    conn.close()
    print(f"✅  Database seeded at {DB_PATH}")
    print(f"    Products:   {len(products)}")
    print(f"    Orders:     {len(orders)}")
    print(f"    Order items: {len(order_items_rows)}")
    print(f"    Exceptions: {len(exceptions_rows)}")


def _status_timestamps(day: datetime, reached_status: str, hour: int, minute: int) -> dict:
    """Build timestamp dict up to the reached status."""
    ts = {
        "created_at": None, "processing_at": None, "ready_to_pick_at": None,
        "picking_at": None, "packed_at": None, "staged_at": None,
        "shipped_at": None, "delivered_at": None,
    }
    base = day.replace(hour=hour, minute=minute)
    flow_keys = [
        ("NEW", "created_at"),
        ("PROCESSING", "processing_at"),
        ("READY_TO_PICK", "ready_to_pick_at"),
        ("PICKING", "picking_at"),
        ("PACKED", "packed_at"),
        ("STAGED", "staged_at"),
        ("SHIPPED", "shipped_at"),
        ("DELIVERED", "delivered_at"),
    ]
    elapsed = 0
    for status_name, key in flow_keys:
        elapsed += random.randint(5, 30)
        ts[key] = (base + timedelta(minutes=elapsed)).isoformat()
        if status_name == reached_status:
            break
    return ts


if __name__ == "__main__":
    seed()
