# 📦 Fulfillment Hub

**Simple Warehouse & Order Fulfillment Operations System for XYZ**

🔗 **Live Application:** https://xyz-fulfillment-app.streamlit.app/  
💻 **Source Code:** https://github.com/the-irritater/fulfillment-hub

---

## Problem

XYZ operates a growing e-commerce fulfillment operation processing **200–300 orders daily** across multiple sales channels. The team currently manages orders through spreadsheets, shared folders, and informal communication, leading to:

- **No centralized order tracking** – Order status is scattered across systems.
- **Delays go unnoticed** – There is no clear SLA or deadline monitoring.
- **Priority orders are missed** – Same-day and urgent orders can get buried.
- **Stock availability is unreliable** – Orders may reach picking before stock problems are identified.
- **Wrong products get shipped** – Similar SKUs and variants can cause picking errors.
- **Boxes can be misplaced** – Staging information is difficult to track.
- **Courier pickups can be missed** – Pickup windows are not actively monitored.
- **Problems can be forgotten** – Issues handled informally have no centralized history.

## Solution

Fulfillment Hub provides the warehouse and office teams with **one clear place to see what needs attention and move orders through fulfillment reliably**.

> **"At any moment, the team should know what needs attention, what is delayed, what can be picked, and what is blocked."**

### Prioritization

I focused on four problems based on operational impact:

| Priority | Problem | Why |
|----------|---------|-----|
| 1 | **Priority/deadline visibility** | Missing same-day shipments directly affects customer experience. |
| 2 | **Inventory availability** | Orders cannot move forward without physical stock. |
| 3 | **Picking accuracy** | Wrong products cause returns, complaints, and additional cost. |
| 4 | **Exception management** | Unresolved issues remain invisible when handled informally. |

> I intentionally did not build real courier integrations or customer-facing features because the primary operational bottleneck is inside the fulfillment workflow. The focus is on giving the warehouse and office teams a single operational source of truth.

---

# How to Use the App

The application is hosted on Streamlit, so **no installation is required to evaluate the live version**.

### Step 1: Open the application

Open the live application:

**https://xyz-fulfillment-app.streamlit.app/**

The application loads with pre-populated sample data representing a realistic fulfillment operation.

### Step 2: Start from the Dashboard

The **Operations Dashboard** is the recommended starting point.

Use it to understand:

- Total orders and priority orders.
- Orders that are urgent or at risk.
- The current fulfillment pipeline.
- Stock and operational blockers.
- Orders requiring immediate attention.
- Upcoming courier pickup windows.

The dashboard is designed around the question:

> **"What needs attention right now?"**

---

### Step 3: Review Orders

Open **Order Management** to search and filter orders.

You can filter orders by:

- Order ID
- Customer
- Priority
- Fulfillment status
- Risk level

Open an individual order to see:

- Customer and order information.
- Items and SKUs.
- Stock availability.
- Warehouse/location codes.
- Fulfillment status.
- Courier information.
- Shipping cost.
- Related issues or exceptions.

Use the **status advancement controls** to move an order through the fulfillment workflow.

---

### Step 4: Check Inventory

Open **Inventory Management** to review stock across the:

- **Main Warehouse**
- **Secondary Warehouse**

The application calculates:

`Available Stock = Main Stock - Reserved Stock`

Inventory is categorized as:

- 🟢 **OK**
- 🟡 **Low**
- 🟠 **Transfer Needed**
- 🔴 **Out of Stock**

If an order requires a product that is unavailable in the Main Warehouse but available in the Secondary Warehouse, you can create a **stock transfer**.

The transfer can then be tracked through its workflow until completion.

---

### Step 5: Perform Picking & Packing

Open **Picking & Packing** to simulate the warehouse workflow.

The picking queue is organized around operational priority.

For each order:

1. Select an order from the picking queue.
2. Review the required items.
3. Check the expected SKU.
4. Check the warehouse location.
5. Select the SKU that was actually picked.
6. Confirm the item.
7. Continue until all items are verified.
8. Complete the picking/packing workflow.

The application compares the **expected SKU against the picked SKU**.

If the wrong SKU is selected, the system automatically detects the mismatch and creates an exception instead of allowing the issue to remain invisible.

---

### Step 6: Handle Exceptions

Open **Exception Management** to review operational problems.

Examples include:

- Stock Shortage
- Wrong SKU
- Box Misplaced
- Courier Missed Pickup
- Other fulfillment issues

Exceptions are prioritized by severity.

A typical workflow is:

**Investigation → Resolution → Recovery**

Each exception can be reviewed, assigned an appropriate priority, and updated with resolution notes.

Once an issue is resolved, the related order can continue through the fulfillment workflow.

---

### Step 7: Follow the Complete Fulfillment Flow

For the best evaluation experience, follow an order through the complete workflow:

```text
Order
  ↓
Processing
  ↓
Ready to Pick
  ↓
Picking
  ↓
Packed
  ↓
Staged
  ↓
Shipped
  ↓
Delivered
```

If an operational problem occurs, the order can enter an exception workflow:

```text
Order Blocked
      ↓
Exception Created
      ↓
Investigation
      ↓
Resolution
      ↓
Order Recovery
      ↓
Continue Fulfillment
```

---

# Recommended Evaluation Scenarios

The sample database intentionally contains operational edge cases. These scenarios demonstrate the main capabilities of the application.

### Scenario 1: Find an Urgent Order

1. Open the **Dashboard**.
2. Look at the **Orders Needing Attention** section.
3. Identify an order marked **URGENT**.
4. Open the order.
5. Review its deadline, priority, stock, and fulfillment status.
6. Advance the order through the workflow where possible.

This demonstrates deadline visibility and priority scoring.

### Scenario 2: Handle a Stock Shortage

1. Open **Inventory**.
2. Find a SKU marked **Transfer Needed** or **Out of Stock**.
3. Review stock in the Main and Secondary Warehouses.
4. Create a transfer when secondary stock is available.
5. Track the transfer.
6. Return to the affected order and continue fulfillment after the stock issue is resolved.

This demonstrates inventory visibility and operational recovery.

### Scenario 3: Detect a Wrong SKU

1. Open **Picking & Packing**.
2. Select an order from the picking queue.
3. Review the expected SKU.
4. Select an incorrect SKU as the picked item.
5. Confirm the selection.
6. Observe that the system detects the mismatch.
7. Open **Exception Management** to review the automatically created exception.

This demonstrates how the system prevents a picking error from silently progressing to shipment.

### Scenario 4: Review a Courier Delay

1. Open the **Dashboard**.
2. Review the courier pickup timeline.
3. Identify an order affected by a pickup delay.
4. Open the related order or exception.
5. Review the issue and update its resolution status.

This demonstrates courier pickup visibility and exception handling.

### Scenario 5: Find an SLA-Breached Order

1. Open the **Dashboard**.
2. Look for an order with an urgent or at-risk risk band.
3. Open the order.
4. Review its ship-by deadline.
5. Check the priority score and contributing factors.
6. Take the appropriate fulfillment action.

This demonstrates deadline monitoring and the rule-based prioritization system.

---

# Priority Scoring

Orders are scored using a transparent rule-based priority system:

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

### Risk Bands

- 🔴 **URGENT** – Score ≥ 60
- 🟠 **AT RISK** – Score 40–59
- 🟢 **ON TRACK** – Score < 40

The scoring system is intentionally transparent so warehouse and office staff can understand **why an order is receiving attention**.

---

# Key Features

## 1. 🏠 Operations Dashboard

- Action-oriented overview focused on what needs attention now.
- KPI metrics for total orders, priority orders, and urgent/at-risk orders.
- Fulfillment pipeline from New to Delivered.
- Blocker summary for stock, picking, packing, and courier issues.
- Priority-scored attention queue.
- Courier pickup timeline.

## 2. 📋 Order Management

- Search and filter by ID, customer, priority, status, and risk level.
- Detailed order view.
- Item-level stock availability.
- Warehouse location codes.
- Fulfillment status stepper.
- Courier information and cost.
- One-click status advancement.
- Issue reporting with automatic exception creation.

## 3. 📦 Inventory Management

- Stock levels across Main and Secondary Warehouses.
- Available stock calculation.
- Inventory health indicators.
- Transfer-needed identification.
- One-click transfer creation.
- Transfer tracking and completion workflow.

## 4. 🛒 Picking & Packing

- Warehouse-friendly interface with large text and controls.
- Priority-sorted picking queue.
- Item-by-item verification.
- SKU and location verification.
- Automatic mismatch detection.
- Automatic exception creation.
- Order-level progress tracking.

## 5. ⚠️ Exception Management

- Centralized issue tracker.
- Stock Shortage, Wrong SKU, Box Misplaced, and Courier Missed Pickup categories.
- Priority-based sorting.
- Investigation and resolution workflow.
- Resolution notes.
- Order recovery after issue resolution.
- Historical exception visibility.

---

# Workflow

```text
Order → Processing → Ready to Pick → Picking → Packed → Staged → Shipped → Delivered
                           ↓              ↓          ↓          ↓
                      STOCK_ISSUE   PICKING_ISSUE  PACKING_ISSUE  COURIER_DELAY
                           ↓              ↓          ↓          ↓
                    Exception → Owner → Investigation → Resolution → Recovery
```

---

# Technology

| Layer | Technology |
|-------|------------|
| Frontend | Streamlit |
| Backend | Python |
| Database | SQLite |
| Data Processing | Pandas |
| Visualization | Plotly |
| Analytics | SQL |

---

# Sample Data

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

- Priority orders with tight deadlines.
- Stock shortages where the Main Warehouse has no stock but the Secondary Warehouse does.
- SKU mismatches during picking.
- Courier pickup delays.
- SLA-breached orders.
- On-hold orders requiring attention.

---

# How to Run Locally

### Prerequisites

- Python 3.9+
- Git

### 1. Clone the repository

```bash
git clone https://github.com/the-irritater/fulfillment-hub.git
cd fulfillment-hub
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

The SQLite database is automatically created and seeded on the first run.

### Reset the sample database

If you want to restore the original sample data:

```bash
rm database/fulfillment.db
streamlit run app.py
```

---

# Project Structure

```text
fulfillment-hub/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── pages/
│   ├── dashboard.py
│   ├── orders.py
│   ├── inventory.py
│   ├── picking.py
│   └── exceptions.py
├── database/
│   ├── schema.sql
│   ├── seed_data.py
│   └── fulfillment.db
├── utils/
│   ├── db.py
│   ├── priority.py
│   ├── inventory.py
│   └── fulfillment.py
└── README.md
```

---

# Design Decisions

### 1. Action dashboard over analytics dashboard

The warehouse team needs to know **"What do I do next?"**, not simply **"What happened last month?"**

Therefore, the dashboard emphasizes operational queues, blockers, deadlines, and priority rather than a large number of historical charts.

### 2. Rule-based priority scoring over ML

A transparent scoring system is easier for warehouse staff to understand and trust than a black-box prediction model.

The goal is not to predict an uncertain future event. It is to identify which existing orders require attention based on known operational conditions.

### 3. SKU verification via dropdown instead of barcode

The assessment environment does not require additional hardware. Dropdown-based SKU verification simulates the core control:

**Expected SKU → Picked SKU → Verification → Exception if mismatched**

A real implementation could replace this input with barcode scanning.

### 4. Large and simple picking interface

The company specifically mentioned that some warehouse workers are not comfortable with technology.

The picking interface therefore uses large controls, limited fields, clear statuses, and simple confirmation steps.

### 5. Automatic exception creation

The system does not rely entirely on workers remembering to report problems.

For example, when the picked SKU does not match the expected SKU, an exception is automatically created.

### 6. Single SQLite database

SQLite keeps the application simple to run and evaluate without requiring separate database infrastructure.

For a production deployment, this could be replaced with a managed relational database and a multi-user backend.

---

# AI Usage

AI was used during development for:

- Brainstorming workflow designs and status models.
- Generating realistic sample data with intentional edge cases.
- Debugging SQL queries and Streamlit layouts.
- Reviewing UI design for warehouse-friendliness.
- Suggesting priority scoring factors.

### Where I disagreed with AI

**1. AI suggested adding ML to predict delays.**

I rejected this because XYZ's primary problem is operational visibility, not prediction. A transparent rule-based deadline and priority system is easier for warehouse staff to understand and act on.

**2. AI suggested creating many dashboard charts.**

I replaced multiple analytical charts with an **"Orders Needing Attention"** queue because the warehouse team needs actionable information rather than analytical complexity.

**3. AI suggested building a full authentication system.**

I excluded this because the assessment focuses on fulfillment operations. Adding authentication would increase implementation complexity without materially improving the demonstration of the core workflow.

---

# Future Improvements

- [ ] Real barcode scanner integration for SKU verification.
- [ ] Courier API integration for live tracking.
- [ ] Mobile-responsive picking interface.
- [ ] Automated email/SMS alerts for SLA breaches.
- [ ] Historical analytics and trend reporting.
- [ ] Multi-user support with role-based access.
- [ ] Batch picking for multiple small orders.
- [ ] Returns and reverse logistics tracking.
- [ ] Production database and API layer for concurrent users.

---

# Evaluation Links

### Live Application

**https://xyz-fulfillment-app.streamlit.app/**

Use the hosted application to explore the workflow without installing anything.

### GitHub Repository

**https://github.com/the-irritater/fulfillment-hub**

The repository contains the complete source code, database schema, seed data, and local setup instructions.

---

## Summary

Fulfillment Hub is designed around one operational principle:

> **At any moment, the team should know what needs attention, what is delayed, what can be picked, and what is blocked.**

Rather than attempting to solve every possible logistics problem, the application focuses on the internal fulfillment workflow where visibility, inventory availability, picking accuracy, deadlines, and exception handling have the most immediate operational impact.
