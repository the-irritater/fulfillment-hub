# 📦 Fulfillment Hub

**Simple Warehouse & Order Fulfillment Operations System for XYZ**

---

## Problem

XYZ operates a growing e-commerce fulfillment operation processing 200–300 orders daily across multiple sales channels. The team currently manages orders through spreadsheets, shared folders, and informal communication, leading to:

- **No centralized order tracking** — Order status is scattered across systems
- **Delays go unnoticed** — No SLA or deadline monitoring
- **Priority orders missed** — No intelligent prioritization
- **Stock unavailable** — Inventory information is unreliable
- **Wrong product shipped** — Picking errors due to similar SKUs/variants
- **Boxes misplaced** — Poor staging area tracking
- **Courier misses pickup** — No pickup window monitoring
- **Problems forgotten** — Issues handled informally with no tracking

## Solution

Fulfillment Hub provides the warehouse and office teams with **one clear place to see what needs attention** and move orders through fulfillment reliably.

> **"At any moment, the team should know what needs attention, what is delayed, what can be picked, and what is blocked."**

### Prioritization

I focused on **four problems** based on operational impact:

| Priority | Problem | Why |
|----------|---------|-----|
| 1 | **Priority/deadline visibility** | Missing same-day shipments directly affects customer experience |
| 2 | **Inventory availability** | Orders cannot move forward without physical stock |
| 3 | **Picking accuracy** | Wrong products cause returns, complaints, and extra cost |
| 4 | **Exception management** | Unresolved issues remain invisible when handled informally |

> I intentionally did not build real courier integrations or customer-facing features because the primary operational bottleneck is inside the fulfillment workflow. I focused on giving the warehouse and office teams a single source of truth.

---

## Key Features

### 1. 🏠 Operations Dashboard
- Action-oriented overview — not just charts, but **what needs attention now**
- KPI metrics: total orders, priority orders, urgent/at-risk counts
- Fulfillment pipeline view (New → Processing → Picking → Packed → Staged → Shipped → Delivered)
- Blocker summary (stock issues, picking issues, courier delays)
- **Priority-scored attention queue** — orders ranked by urgency
- Courier pickup timeline with countdown

### 2. 📋 Order Management
- Search and filter by ID, customer, priority, status, risk level
- Detailed order view with item listing, stock availability, and location codes
- Fulfillment status stepper with timestamps
- Courier information and cost
- One-click status advancement
- Issue reporting with auto-exception creation

### 3. 📦 Inventory Management
- Stock levels across Main and Secondary warehouses
- Availability calculation: `Available = Main Stock - Reserved`
- Color-coded status: OK / Low / Transfer Needed / Out of Stock
- One-click transfer creation (Secondary → Main)
- Transfer tracking and completion workflow

### 4. 🛒 Picking & Packing
- Warehouse-friendly interface with **large text and buttons**
- Priority-sorted picking queue
- Item-by-item verification with location codes
- **SKU verification** — confirms expected vs. picked SKU
- Automatic mismatch detection and exception creation
- Progress tracking per order

### 5. ⚠️ Exception Management
- Centralized issue tracker: Stock Shortage, Wrong SKU, Box Misplaced, Courier Missed Pickup
- Priority-based sorting (High → Medium → Low)
- Investigation → Resolution workflow with notes
- Automatic order recovery when exceptions are resolved
- Full history of resolved exceptions

---

## Workflow

```
Order → Processing → Ready to Pick → Picking → Packed → Staged → Shipped → Delivered
                          ↓              ↓          ↓          ↓
                     STOCK_ISSUE   PICKING_ISSUE  PACKING_ISSUE  COURIER_DELAY
                          ↓              ↓          ↓          ↓
                     Exception → Owner → Investigation → Resolution → Recovery
```

## Priority Scoring

Orders are scored using a rule-based priority system:

| Factor | Points |
|--------|--------|
| Priority order (High) | +30 |
| SLA breached (deadline passed) | +40 |
| Deadline < 2 hours | +30 |
| Deadline < 4 hours | +15 |
| Stock issue / On hold | +25 |
| Active exception | +20 |
| Picking / Packing issue | +20 |
| Courier pickup < 1 hour | +15 |

**Risk Bands:**
- 🔴 **URGENT** — Score ≥ 60
- 🟠 **AT RISK** — Score 40–59
- 🟢 **ON TRACK** — Score < 40

---

## Technology

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | Python |
| Database | SQLite |
| Data Processing | Pandas |
| Visualization | Plotly |
| Analytics | SQL |

---

## Sample Data

The application is pre-loaded with realistic operational data:

| Data | Volume |
|------|--------|
| Products/SKUs | ~80 |
| Historical orders | ~1,250 |
| Today's orders | ~250 |
| Order items | ~3,500+ |
| Inventory records | ~160 (80 SKUs × 2 warehouses) |
| Couriers | 5 |
| Exceptions | ~60+ |

### Built-in Scenarios

The sample data intentionally includes:

- ✅ **Priority orders** — High-priority with tight deadlines
- ✅ **Stock shortages** — Main warehouse at 0, secondary has stock
- ✅ **SKU mismatches** — Wrong SKU picked during fulfillment
- ✅ **Courier delays** — Missed pickup windows
- ✅ **SLA breaches** — Orders past their ship-by deadline
- ✅ **On-hold orders** — Blocked orders needing attention

---

## How to Run

```bash
# Clone the repository
git clone <repo-url>
cd fulfillment-hub

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The database is automatically created and seeded on first run.

To reset the data:
```bash
rm database/fulfillment.db
streamlit run app.py
```

---

## Project Structure

```
fulfillment-hub/
├── app.py                    # Main Streamlit application
├── requirements.txt
├── .streamlit/
│   └── config.toml           # Theme configuration
├── pages/
│   ├── dashboard.py          # Operations Dashboard
│   ├── orders.py             # Order Management
│   ├── inventory.py          # Inventory Management
│   ├── picking.py            # Picking & Packing
│   └── exceptions.py         # Exception Management
├── database/
│   ├── schema.sql            # Database schema
│   ├── seed_data.py          # Sample data generator
│   └── fulfillment.db        # SQLite database (auto-created)
├── utils/
│   ├── db.py                 # Database connection helper
│   ├── priority.py           # Priority scoring engine
│   ├── inventory.py          # Inventory functions
│   └── fulfillment.py        # Order/fulfillment functions
└── README.md
```

---

## Design Decisions

1. **Action dashboard over analytics dashboard** — The warehouse team needs to know "what do I do next?", not "what happened last month?"

2. **Rule-based priority scoring over ML** — A transparent, understandable scoring system is easier for warehouse staff to trust and act on than a black-box prediction model.

3. **SKU verification via dropdown, not barcode** — Simulates the verification workflow without requiring hardware. Demonstrates how picking errors would be caught.

4. **Large, simple UI for picking** — The company specifically mentioned warehouse workers aren't comfortable with technology. Large text, minimal fields, clear confirmations.

5. **Automatic exception creation on mismatches** — Instead of relying on workers to report issues, the system detects and tracks them automatically.

6. **Single SQLite database** — No server setup required. Evaluators can run the app with zero configuration.

---

## AI Usage

AI was used during development for:
- Brainstorming workflow designs and status models
- Generating realistic sample data with intentional edge cases
- Debugging SQL queries and Streamlit layouts
- Reviewing UI design for warehouse-friendliness
- Suggesting priority scoring factors

### Where I disagreed with AI:

**1. AI suggested adding ML to predict delays.**
> I rejected this because XYZ's primary problem is operational visibility, not prediction. A transparent rule-based deadline/priority system is easier for warehouse staff to understand and act on.

**2. AI suggested creating many dashboard charts.**
> I replaced multiple analytical charts with an "Orders Needing Attention" queue. The warehouse team needs actionable information, not analytical complexity.

**3. AI suggested building a full authentication system.**
> I excluded it because this is an internal operations tool for a small team. Adding auth would increase complexity without demonstrating operational problem-solving.

---

## Future Improvements

- [ ] Real barcode scanner integration for SKU verification
- [ ] Courier API integration for live tracking
- [ ] Mobile-responsive picking interface
- [ ] Automated alerts (email/SMS) for SLA breaches
- [ ] Historical analytics and trend reporting
- [ ] Multi-user support with role-based access
- [ ] Batch picking for multiple small orders
- [ ] Returns and reverse logistics tracking
