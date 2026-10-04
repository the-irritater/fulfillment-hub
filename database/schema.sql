-- Fulfillment Hub Database Schema
-- SQLite

-- Products / SKU catalog
CREATE TABLE IF NOT EXISTS products (
    product_id   TEXT PRIMARY KEY,
    sku          TEXT UNIQUE NOT NULL,
    product_name TEXT NOT NULL,
    variant      TEXT,
    category     TEXT,
    weight_kg    REAL DEFAULT 0.5,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Inventory across warehouses
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT NOT NULL REFERENCES products(sku),
    warehouse       TEXT NOT NULL CHECK(warehouse IN ('Main','Secondary')),
    quantity         INTEGER NOT NULL DEFAULT 0,
    reserved        INTEGER NOT NULL DEFAULT 0,
    location_code   TEXT,  -- e.g. A-03-12
    last_updated    TEXT DEFAULT (datetime('now')),
    UNIQUE(sku, warehouse)
);

-- Couriers
CREATE TABLE IF NOT EXISTS couriers (
    courier_id      TEXT PRIMARY KEY,
    courier_name    TEXT NOT NULL,
    cost_per_order  REAL NOT NULL,
    pickup_time     TEXT NOT NULL,          -- HH:MM
    delivery_days   INTEGER NOT NULL,
    contact_phone   TEXT,
    is_active       INTEGER DEFAULT 1
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    channel         TEXT NOT NULL CHECK(channel IN ('Amazon','Flipkart','Website','Wholesale','Walk-in')),
    priority        TEXT NOT NULL DEFAULT 'Normal' CHECK(priority IN ('High','Normal')),
    order_date      TEXT NOT NULL,           -- date
    order_time      TEXT NOT NULL,           -- HH:MM
    ship_by         TEXT NOT NULL,           -- datetime ISO
    status          TEXT NOT NULL DEFAULT 'NEW'
                    CHECK(status IN (
                        'NEW','PROCESSING','READY_TO_PICK','PICKING',
                        'PACKED','STAGED','SHIPPED','DELIVERED',
                        'ON_HOLD','STOCK_ISSUE','PICKING_ISSUE',
                        'PACKING_ISSUE','COURIER_DELAY','CANCELLED'
                    )),
    warehouse       TEXT DEFAULT 'Main',
    courier_id      TEXT REFERENCES couriers(courier_id),
    tracking_number TEXT,
    assigned_picker TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    processing_at   TEXT,
    ready_to_pick_at TEXT,
    picking_at      TEXT,
    packed_at       TEXT,
    staged_at       TEXT,
    shipped_at      TEXT,
    delivered_at    TEXT,
    notes           TEXT
);

-- Order line items
CREATE TABLE IF NOT EXISTS order_items (
    item_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    TEXT NOT NULL REFERENCES orders(order_id),
    sku         TEXT NOT NULL REFERENCES products(sku),
    quantity    INTEGER NOT NULL DEFAULT 1,
    picked_sku  TEXT,              -- what was actually picked (for verification)
    pick_status TEXT DEFAULT 'PENDING'
                CHECK(pick_status IN ('PENDING','CONFIRMED','MISMATCH')),
    UNIQUE(order_id, sku)
);

-- Exceptions / Issues
CREATE TABLE IF NOT EXISTS exceptions (
    exception_id    TEXT PRIMARY KEY,
    order_id        TEXT REFERENCES orders(order_id),
    exception_type  TEXT NOT NULL
                    CHECK(exception_type IN (
                        'STOCK_SHORTAGE','WRONG_SKU','BOX_MISPLACED',
                        'COURIER_MISSED_PICKUP','DAMAGED_ITEM',
                        'ADDRESS_ISSUE','OTHER'
                    )),
    priority        TEXT NOT NULL DEFAULT 'Medium'
                    CHECK(priority IN ('High','Medium','Low')),
    status          TEXT NOT NULL DEFAULT 'Open'
                    CHECK(status IN ('Open','Investigating','Resolved','Closed')),
    owner           TEXT,
    description     TEXT,
    resolution      TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    resolved_at     TEXT
);

-- Inventory transfers between warehouses
CREATE TABLE IF NOT EXISTS transfers (
    transfer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT NOT NULL,
    from_warehouse  TEXT NOT NULL,
    to_warehouse    TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    status          TEXT DEFAULT 'REQUESTED'
                    CHECK(status IN ('REQUESTED','IN_TRANSIT','COMPLETED','CANCELLED')),
    requested_at    TEXT DEFAULT (datetime('now')),
    completed_at    TEXT
);

-- Fulfillment event log (audit trail)
CREATE TABLE IF NOT EXISTS fulfillment_events (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    TEXT NOT NULL REFERENCES orders(order_id),
    event_type  TEXT NOT NULL,
    event_detail TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    created_by  TEXT DEFAULT 'system'
);
