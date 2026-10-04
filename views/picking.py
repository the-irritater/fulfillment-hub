"""
Picking & Packing page — Warehouse worker interface.

Designed for users who are NOT comfortable with technology:
  • Large text and buttons
  • Minimal information per screen
  • Clear confirmation flow
  • SKU verification built in
"""

import streamlit as st
import pandas as pd

from utils.fulfillment import (
    get_picking_queue, get_order_detail, confirm_pick,
    update_order_status,
)
from utils.priority import deadline_display, risk_emoji, risk_band
from utils.db import run_query


def render():
    st.markdown('<div class="hub-header">🛒 Picking & Packing</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hub-subtitle">'
        'Pick items accurately • Verify SKUs • Confirm packing'
        '</div>',
        unsafe_allow_html=True,
    )

    # Check if we're in picking mode for a specific order
    if "picking_order" in st.session_state and st.session_state["picking_order"]:
        _render_picking_screen(st.session_state["picking_order"])
        return

    # ------------------------------------------------------------------
    # Picking Queue
    # ------------------------------------------------------------------
    st.markdown("#### 📋 Picking Queue")
    st.markdown("Orders ready to be picked, sorted by priority and deadline.")

    queue = get_picking_queue()

    if not queue:
        st.success("✅ No orders waiting to be picked!")
        st.balloons()
        return

    # Summary
    mc1, mc2, mc3 = st.columns(3)
    ready = sum(1 for o in queue if o["status"] == "READY_TO_PICK")
    picking = sum(1 for o in queue if o["status"] == "PICKING")
    high_pri = sum(1 for o in queue if o["priority"] == "High")
    mc1.metric("Ready to Pick", ready)
    mc2.metric("Currently Picking", picking)
    mc3.metric("🔴 High Priority", high_pri)

    st.markdown("---")

    for o in queue:
        dl = deadline_display(o["ship_by"])
        priority_badge = "🔴 HIGH" if o["priority"] == "High" else ""
        status_display = o["status"].replace("_", " ")
        css = "exc-high" if o["priority"] == "High" else "exc-low"

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"""
            <div class="{css}">
                <div style="font-size:1.3rem; font-weight:700;">
                    {priority_badge} {o['order_id']}
                </div>
                <div style="margin-top:4px;">
                    {o['customer_name']}
                    &nbsp;•&nbsp;
                    {o['item_count']} item(s)
                    &nbsp;•&nbsp;
                    {status_display}
                    &nbsp;•&nbsp;
                    {dl}
                </div>
                <div style="margin-top:4px; opacity:0.6;">
                    Picker: {o.get('assigned_picker') or 'Unassigned'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("")
            st.markdown("")
            if o["status"] == "READY_TO_PICK":
                if st.button("🛒 START", key=f"start_{o['order_id']}",
                             use_container_width=True):
                    update_order_status(o["order_id"], "PICKING")
                    st.session_state["picking_order"] = o["order_id"]
                    st.rerun()
            else:
                if st.button("▶ CONTINUE", key=f"cont_{o['order_id']}",
                             use_container_width=True):
                    st.session_state["picking_order"] = o["order_id"]
                    st.rerun()


def _render_picking_screen(order_id: str):
    """
    Large, simple picking interface for warehouse workers.
    One item at a time, clear SKU verification.
    """
    if st.button("← Back to Queue", use_container_width=False):
        st.session_state["picking_order"] = None
        st.rerun()

    order = get_order_detail(order_id)
    if not order:
        st.error(f"Order {order_id} not found.")
        return

    # Header
    st.markdown(f"""
    <div class="hub-card" style="text-align:center;">
        <div style="font-size:1.1rem; opacity:0.6;">PICKING ORDER</div>
        <div style="font-size:2.5rem; font-weight:800; color:#a78bfa;">
            {order_id}
        </div>
        <div style="font-size:1.1rem; margin-top:4px;">
            {order['customer_name']} &nbsp;•&nbsp; {deadline_display(order['ship_by'])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    items = order["items"]
    total = len(items)
    confirmed = sum(1 for it in items if it["pick_status"] == "CONFIRMED")
    mismatched = sum(1 for it in items if it["pick_status"] == "MISMATCH")
    pending = sum(1 for it in items if it["pick_status"] == "PENDING")

    # Progress bar
    progress = confirmed / total if total > 0 else 0
    st.progress(progress, text=f"✅ {confirmed}/{total} items confirmed")

    if mismatched > 0:
        st.error(f"❌ {mismatched} item(s) have SKU mismatches!")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Show each item with large, clear UI
    # ------------------------------------------------------------------
    for idx, item in enumerate(items):
        status_emoji_map = {
            "CONFIRMED": "✅",
            "MISMATCH": "❌",
            "PENDING": "📋",
        }
        s_emoji = status_emoji_map.get(item["pick_status"], "📋")

        if item["pick_status"] == "CONFIRMED":
            card_style = "border-left: 4px solid #22c55e; background: rgba(34,197,94,0.06);"
        elif item["pick_status"] == "MISMATCH":
            card_style = "border-left: 4px solid #ef4444; background: rgba(239,68,68,0.06);"
        else:
            card_style = "border-left: 4px solid #6C63FF; background: rgba(108,99,255,0.06);"

        st.markdown(f"""
        <div style="{card_style} border-radius:0 12px 12px 0; padding:20px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-size:0.85rem; opacity:0.5;">
                        ITEM {idx + 1} of {total} &nbsp;•&nbsp; {s_emoji} {item['pick_status']}
                    </div>
                    <div style="font-size:1.6rem; font-weight:800; color:#a78bfa; margin-top:4px;">
                        {item['sku']}
                    </div>
                    <div style="font-size:1.2rem; margin-top:4px;">
                        {item['product_name']}
                    </div>
                    <div style="font-size:1.05rem; opacity:0.75;">
                        {item['variant']}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:2rem; font-weight:800;">
                        Qty: {item['quantity']}
                    </div>
                    <div style="font-size:1.2rem; font-weight:600; color:#6C63FF; margin-top:8px;">
                        📍 {item.get('location_code', '—')}
                    </div>
                    <div style="font-size:0.9rem; opacity:0.5; margin-top:4px;">
                        Stock: {item.get('available_stock', '?')}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # SKU verification for pending items
        if item["pick_status"] == "PENDING":
            vc1, vc2 = st.columns([3, 1])
            with vc1:
                # Get all SKUs for the dropdown
                all_skus = run_query("SELECT sku FROM products ORDER BY sku")
                sku_list = [s["sku"] for s in all_skus]
                default_idx = sku_list.index(item["sku"]) if item["sku"] in sku_list else 0

                picked = st.selectbox(
                    f"Verify SKU for Item {idx + 1}",
                    sku_list,
                    index=default_idx,
                    key=f"pick_sku_{order_id}_{item['sku']}",
                )
            with vc2:
                st.markdown("")
                st.markdown("")
                if st.button("✅ CONFIRM PICK", key=f"confirm_{order_id}_{item['sku']}",
                             use_container_width=True):
                    result = confirm_pick(order_id, item["sku"], picked)
                    if result == "CONFIRMED":
                        st.success(f"✅ {item['sku']} — Match confirmed!")
                    else:
                        st.error(
                            f"❌ SKU MISMATCH!\n\n"
                            f"**Expected:** {item['sku']}\n\n"
                            f"**Picked:** {picked}\n\n"
                            f"An exception has been created."
                        )
                    st.rerun()

        elif item["pick_status"] == "MISMATCH":
            st.markdown(f"""
            <div style="background:rgba(239,68,68,0.1); padding:12px; border-radius:8px;
                        border:1px solid rgba(239,68,68,0.3); margin-bottom:12px;">
                ❌ <strong>MISMATCH</strong><br>
                Expected: <strong>{item['sku']}</strong><br>
                Picked: <strong>{item.get('picked_sku', '?')}</strong><br>
                <em>Exception has been reported.</em>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Retry Pick", key=f"retry_{order_id}_{item['sku']}"):
                from utils.fulfillment import retry_pick
                retry_pick(order_id, item["sku"])
                st.rerun()

    # ------------------------------------------------------------------
    # Complete picking
    # ------------------------------------------------------------------
    st.markdown("---")
    if confirmed == total and total > 0:
        st.success("🎉 All items confirmed! Ready to pack.")
        if st.button("📦 MARK ORDER PACKED", use_container_width=True):
            update_order_status(order_id, "PACKED")
            st.session_state["picking_order"] = None
            st.success(f"Order {order_id} marked as PACKED!")
            st.rerun()
    elif pending == 0 and mismatched > 0:
        st.warning(
            f"⚠️ {mismatched} item(s) have mismatches. "
            f"Resolve issues before completing."
        )
    else:
        st.info(f"📋 {pending} item(s) still need to be picked and verified.")
