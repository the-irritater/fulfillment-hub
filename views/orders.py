"""
Orders page — Search, filter, view details, and update order status.
"""

import streamlit as st
import pandas as pd

from utils.fulfillment import (
    get_filtered_orders, get_order_detail, update_order_status,
    next_status, STATUS_FLOW, EXCEPTION_STATUSES,
)
from utils.priority import risk_emoji, deadline_display, current_time
from utils.inventory import check_stock_for_order
from utils.db import run_query


def render():
    st.markdown('<div class="hub-header">📋 Order Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="hub-subtitle">Search, filter, and manage fulfillment orders</div>',
                unsafe_allow_html=True)

    # Check if we're in detail view
    if "view_order" in st.session_state and st.session_state["view_order"]:
        _render_order_detail(st.session_state["view_order"])
        return

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
    with fc1:
        search = st.text_input("🔍 Search Order ID or Customer", placeholder="ORD1042 or Rahul...")
    with fc2:
        priority_filter = st.selectbox("Priority", ["All", "High", "Normal"])
    with fc3:
        all_statuses = ["All"] + STATUS_FLOW + EXCEPTION_STATUSES
        status_filter = st.selectbox("Status", all_statuses)
    with fc4:
        risk_filter = st.selectbox("Risk", ["All", "URGENT", "AT RISK", "ON TRACK"])

    # Fetch orders
    orders = get_filtered_orders(
        status_filter=status_filter if status_filter != "All" else None,
        priority_filter=priority_filter if priority_filter != "All" else None,
        risk_filter=risk_filter if risk_filter != "All" else None,
        search=search if search else None,
        today_only=True,
    )

    st.markdown(f"**{len(orders)} orders found**")

    if not orders:
        st.info("No orders match the current filters.")
        return

    # ------------------------------------------------------------------
    # Order table
    # ------------------------------------------------------------------
    for o in orders:
        emoji = risk_emoji(o["risk"])
        dl = deadline_display(o["ship_by"])
        priority_badge = "🔴 High" if o["priority"] == "High" else "Normal"
        status_display = o["status"].replace("_", " ")

        # Stock check indicator
        stock_ok = "✓"
        if o["status"] in ("STOCK_ISSUE",):
            stock_ok = "❌"
        elif o["exc_count"] > 0:
            stock_ok = "⚠️"

        css_class = {
            "URGENT": "exc-high",
            "AT RISK": "exc-medium",
            "ON TRACK": "exc-low",
        }.get(o["risk"], "exc-low")

        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"""
            <div class="{css_class}" style="cursor:pointer;">
                <span style="font-weight:700; font-size:1.05rem;">{o['order_id']}</span>
                &nbsp;&nbsp;
                <span>{priority_badge}</span>
                &nbsp;•&nbsp;
                <span style="font-weight:500;">{status_display}</span>
                &nbsp;•&nbsp;
                <span>Stock: {stock_ok}</span>
                &nbsp;•&nbsp;
                <span>{dl}</span>
                &nbsp;•&nbsp;
                <span>{emoji} {o['risk']}</span>
                &nbsp;&nbsp;
                <span style="opacity:0.5; float:right;">
                    {o['customer_name']} • {o['channel']}
                </span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("View", key=f"view_{o['order_id']}"):
                st.session_state["view_order"] = o["order_id"]
                st.rerun()


def _render_order_detail(order_id: str):
    """Render detailed order view."""
    # Back button
    if st.button("← Back to Orders"):
        st.session_state["view_order"] = None
        st.rerun()

    order = get_order_detail(order_id)
    if not order:
        st.error(f"Order {order_id} not found.")
        return

    emoji = risk_emoji(order["risk"])

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    st.markdown(f"""
    <div class="hub-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:1.8rem; font-weight:800; color:#a78bfa;">
                    {order_id}
                </div>
                <div style="opacity:0.7; margin-top:4px;">
                    {order['customer_name']} &nbsp;•&nbsp; {order['channel']}
                </div>
            </div>
            <div style="text-align:right;">
                <div class="status-{'urgent' if order['risk']=='URGENT' else 'at-risk' if order['risk']=='AT RISK' else 'on-track'}">
                    {emoji} {order['risk']} (Score: {order['score']})
                </div>
                <div style="margin-top:8px; font-weight:600;">
                    {deadline_display(order['ship_by'])}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Info columns
    # ------------------------------------------------------------------
    ic1, ic2, ic3, ic4 = st.columns(4)
    ic1.metric("Priority", order["priority"])
    ic2.metric("Status", order["status"].replace("_", " "))
    ic3.metric("Warehouse", order["warehouse"])
    ic4.metric("Picker", order.get("assigned_picker") or "—")

    st.markdown("")

    # ------------------------------------------------------------------
    # Order items
    # ------------------------------------------------------------------
    st.markdown("#### 📦 Order Items")
    items = order["items"]
    if items:
        for item in items:
            avail = item.get("available_stock", 0)
            stock_icon = "✅" if avail >= item["quantity"] else "❌"
            pick_icon = {
                "CONFIRMED": "✅",
                "MISMATCH": "❌",
                "PENDING": "⏳",
            }.get(item["pick_status"], "⏳")

            st.markdown(f"""
            <div class="pick-item">
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <div class="pick-sku">{item['sku']}</div>
                        <div class="pick-product">
                            {item['product_name']} — {item['variant']}
                        </div>
                        <div class="pick-location">
                            📍 Location: {item.get('location_code', '—')}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div>Qty: <strong>{item['quantity']}</strong></div>
                        <div>Stock: {stock_icon} ({avail})</div>
                        <div>Pick: {pick_icon} {item['pick_status']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Fulfillment status stepper
    # ------------------------------------------------------------------
    st.markdown("#### 🔄 Fulfillment Status")
    current = order["status"]
    reached = False
    steps_html = ""
    for s in STATUS_FLOW:
        ts_key = {
            "NEW": "created_at", "PROCESSING": "processing_at",
            "READY_TO_PICK": "ready_to_pick_at", "PICKING": "picking_at",
            "PACKED": "packed_at", "STAGED": "staged_at",
            "SHIPPED": "shipped_at", "DELIVERED": "delivered_at",
        }.get(s, "")
        ts_val = order.get(ts_key, "")

        if s == current:
            steps_html += f'<div class="step-current">● {s.replace("_"," ")}'
            if ts_val:
                steps_html += f' <span style="font-size:0.8em; opacity:0.6;">({ts_val[:16]})</span>'
            steps_html += "</div>"
            reached = True
        elif not reached:
            steps_html += f'<div class="step-done">✓ {s.replace("_"," ")}'
            if ts_val:
                steps_html += f' <span style="font-size:0.8em; opacity:0.6;">({ts_val[:16]})</span>'
            steps_html += "</div>"
        else:
            steps_html += f'<div class="step-pending">○ {s.replace("_"," ")}</div>'

    # Show exception status if applicable
    if current in EXCEPTION_STATUSES:
        steps_html += f'<div class="step-current" style="color:#ef4444;">⚠ {current.replace("_"," ")}</div>'

    st.markdown(f'<div class="hub-card">{steps_html}</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Courier info
    # ------------------------------------------------------------------
    st.markdown("#### 🚚 Courier")
    
    if current in ("NEW", "PROCESSING", "READY_TO_PICK", "PICKING", "PACKED"):
        all_couriers = run_query("SELECT * FROM couriers WHERE is_active = 1")
        courier_opts = {c["courier_id"]: f"{c['courier_name']} (₹{c['cost_per_order']}, {c['delivery_days']} days)" for c in all_couriers}
        
        current_c_id = order.get("courier_id")
        c_ids = list(courier_opts.keys())
        idx = c_ids.index(current_c_id) if current_c_id in c_ids else 0
            
        selected_c_id = st.selectbox("Assign Courier", c_ids, format_func=lambda x: courier_opts[x], index=idx, key=f"courier_sel_{order_id}")
        
        if selected_c_id != current_c_id:
            if st.button("💾 Update Courier"):
                run_execute("UPDATE orders SET courier_id = ? WHERE order_id = ?", (selected_c_id, order_id))
                st.success("Courier updated!")
                st.rerun()
    else:
        cc1, cc2, cc3, cc4 = st.columns(4)
        cc1.metric("Courier", order.get("courier_name") or "—")
        cc2.metric("Pickup Time", order.get("courier_pickup") or "—")
        cc3.metric("Cost", f"₹{order.get('courier_cost', 0)}")
        cc4.metric("Delivery", f"{order.get('delivery_days', '—')} days")

    # ------------------------------------------------------------------
    # Exceptions
    # ------------------------------------------------------------------
    if order["exceptions"]:
        st.markdown("#### ⚠️ Exceptions")
        for exc in order["exceptions"]:
            css = "exc-high" if exc["priority"] == "High" else "exc-medium"
            st.markdown(f"""
            <div class="{css}">
                <strong>{exc['exception_id']}</strong> &nbsp;•&nbsp;
                {exc['exception_type'].replace('_',' ')} &nbsp;•&nbsp;
                Status: {exc['status']} &nbsp;•&nbsp;
                Owner: {exc.get('owner', '—')}
                <div style="margin-top:4px; opacity:0.7; font-size:0.9rem;">
                    {exc.get('description', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    st.markdown("#### 🎬 Actions")
    ac1, ac2, ac3 = st.columns(3)

    nxt = next_status(current)
    if nxt:
        with ac1:
            label_map = {
                "PROCESSING": "Start Processing",
                "READY_TO_PICK": "Mark Ready to Pick",
                "PICKING": "Start Picking",
                "PACKED": "Mark Packed",
                "STAGED": "Move to Staging",
                "SHIPPED": "Mark Shipped",
                "DELIVERED": "Mark Delivered",
            }
            btn_label = label_map.get(nxt, f"Move to {nxt}")
            
            # P1: Enforce valid order-state transitions
            is_valid = True
            error_msg = ""
            
            if nxt == "PACKED":
                # Ensure all items are confirmed
                unconfirmed = sum(1 for it in items if it.get("pick_status") != "CONFIRMED")
                if unconfirmed > 0:
                    is_valid = False
                    error_msg = f"{unconfirmed} item(s) unconfirmed"
            elif nxt == "READY_TO_PICK":
                # Check if stock is sufficient
                insufficient = sum(1 for it in items if (it.get("available_stock") or 0) < it["quantity"])
                if insufficient > 0:
                    is_valid = False
                    error_msg = "Insufficient stock"
            
            if not is_valid:
                st.button(f"🚫 Cannot {btn_label} ({error_msg})", disabled=True, use_container_width=True)
            else:
                if st.button(f"✅ {btn_label}", use_container_width=True):
                    update_order_status(order_id, nxt)
                    st.success(f"Order updated to {nxt}")
                    st.rerun()

    if current in EXCEPTION_STATUSES:
        with ac2:
            # Allow returning to normal flow
            recovery_map = {
                "STOCK_ISSUE": "PROCESSING",
                "ON_HOLD": "PROCESSING",
                "PICKING_ISSUE": "READY_TO_PICK",
                "PACKING_ISSUE": "PICKING",
                "COURIER_DELAY": "STAGED",
            }
            recover_to = recovery_map.get(current, "PROCESSING")
            if st.button(f"🔄 Resolve → {recover_to}", use_container_width=True):
                update_order_status(order_id, recover_to)
                st.success(f"Order recovered to {recover_to}")
                st.rerun()

    with ac3:
        if current not in ("DELIVERED", "CANCELLED"):
            if st.button("🚨 Report Issue", use_container_width=True):
                st.session_state[f"report_issue_{order_id}"] = True
                st.rerun()

    # Issue reporting form
    if st.session_state.get(f"report_issue_{order_id}"):
        with st.form(f"issue_form_{order_id}"):
            st.markdown("##### Report an Issue")
            issue_type = st.selectbox("Issue Type", [
                "STOCK_SHORTAGE", "WRONG_SKU", "BOX_MISPLACED",
                "COURIER_MISSED_PICKUP", "DAMAGED_ITEM", "ADDRESS_ISSUE", "OTHER",
            ])
            issue_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            issue_desc = st.text_area("Description")
            issue_owner = st.text_input("Assign to", value="Warehouse")

            if st.form_submit_button("Submit Issue"):
                from utils.db import run_execute
                exc_count = run_query("SELECT COUNT(*) AS cnt FROM exceptions")[0]["cnt"]
                run_execute(
                    "INSERT INTO exceptions (exception_id, order_id, exception_type, "
                    "priority, status, owner, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (f"EX{exc_count + 1:04d}", order_id, issue_type,
                     issue_priority, "Open", issue_owner, issue_desc),
                )
                # Update order status if appropriate
                status_map = {
                    "STOCK_SHORTAGE": "STOCK_ISSUE",
                    "WRONG_SKU": "PICKING_ISSUE",
                    "BOX_MISPLACED": "PACKING_ISSUE",
                    "COURIER_MISSED_PICKUP": "COURIER_DELAY",
                }
                new_status = status_map.get(issue_type)
                if new_status:
                    update_order_status(order_id, new_status)

                st.session_state[f"report_issue_{order_id}"] = False
                st.success("Issue reported successfully!")
                st.rerun()
