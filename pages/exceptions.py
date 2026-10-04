"""
Exceptions page — Track, manage, and resolve operational issues.

Addresses the company's problem:
  "Problems are handled informally and are easy to forget."
"""

import streamlit as st
import pandas as pd

from utils.db import run_query, run_execute
from utils.priority import current_time


def render():
    st.markdown('<div class="hub-header">⚠️ Exception Management</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hub-subtitle">'
        'Track, assign, and resolve operational issues — nothing gets forgotten'
        '</div>',
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Summary metrics
    # ------------------------------------------------------------------
    all_exc = run_query(
        "SELECT status, priority, COUNT(*) AS cnt "
        "FROM exceptions GROUP BY status, priority"
    )
    open_high = sum(r["cnt"] for r in all_exc
                    if r["status"] in ("Open", "Investigating") and r["priority"] == "High")
    open_med = sum(r["cnt"] for r in all_exc
                   if r["status"] in ("Open", "Investigating") and r["priority"] == "Medium")
    open_low = sum(r["cnt"] for r in all_exc
                   if r["status"] in ("Open", "Investigating") and r["priority"] == "Low")
    resolved = sum(r["cnt"] for r in all_exc if r["status"] in ("Resolved", "Closed"))
    total_open = open_high + open_med + open_low

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🔴 Open (High)", open_high)
    m2.metric("🟠 Open (Medium)", open_med)
    m3.metric("🟢 Open (Low)", open_low)
    m4.metric("Total Open", total_open)
    m5.metric("✅ Resolved", resolved)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
    with fc1:
        search = st.text_input("🔍 Search Exception or Order ID",
                               placeholder="EX0001 or ORD1042...")
    with fc2:
        type_options = ["All", "STOCK_SHORTAGE", "WRONG_SKU", "BOX_MISPLACED",
                        "COURIER_MISSED_PICKUP", "DAMAGED_ITEM", "ADDRESS_ISSUE", "OTHER"]
        type_filter = st.selectbox("Type", type_options)
    with fc3:
        status_filter = st.selectbox("Status",
                                     ["All", "Open", "Investigating", "Resolved", "Closed"])
    with fc4:
        priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"],
                                       key="exc_pri")

    # Build query
    conditions = []
    params = []
    if search:
        conditions.append("(e.exception_id LIKE ? OR e.order_id LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if type_filter != "All":
        conditions.append("e.exception_type = ?")
        params.append(type_filter)
    if status_filter != "All":
        conditions.append("e.status = ?")
        params.append(status_filter)
    if priority_filter != "All":
        conditions.append("e.priority = ?")
        params.append(priority_filter)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    exceptions = run_query(f"""
        SELECT e.*, o.customer_name, o.channel, o.status AS order_status
        FROM exceptions e
        LEFT JOIN orders o ON e.order_id = o.order_id
        {where}
        ORDER BY
            CASE e.status
                WHEN 'Open' THEN 0
                WHEN 'Investigating' THEN 1
                WHEN 'Resolved' THEN 2
                WHEN 'Closed' THEN 3
            END,
            CASE e.priority
                WHEN 'High' THEN 0
                WHEN 'Medium' THEN 1
                WHEN 'Low' THEN 2
            END,
            e.created_at DESC
    """, tuple(params))

    st.markdown(f"**{len(exceptions)} exceptions**")
    st.markdown("")

    if not exceptions:
        st.success("✅ No exceptions match the current filters!")
        return

    # ------------------------------------------------------------------
    # Exception cards
    # ------------------------------------------------------------------
    for exc in exceptions:
        css = {
            "High": "exc-high",
            "Medium": "exc-medium",
            "Low": "exc-low",
        }.get(exc["priority"], "exc-medium")

        priority_emoji = {
            "High": "🔴",
            "Medium": "🟠",
            "Low": "🟢",
        }.get(exc["priority"], "⚪")

        type_display = exc["exception_type"].replace("_", " ").title()
        status_badge = exc["status"]

        st.markdown(f"""
        <div class="{css}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-size:1.15rem; font-weight:700;">
                        {priority_emoji} {exc['exception_id']}
                        &nbsp;•&nbsp; {type_display}
                    </div>
                    <div style="margin-top:4px;">
                        Order: <strong>{exc['order_id']}</strong>
                        &nbsp;•&nbsp;
                        {exc.get('customer_name', '')}
                        &nbsp;•&nbsp;
                        {exc.get('channel', '')}
                    </div>
                    <div style="margin-top:4px; opacity:0.75;">
                        {exc.get('description', '')}
                    </div>
                    <div style="margin-top:4px; font-size:0.85rem; opacity:0.5;">
                        Owner: {exc.get('owner', '—')}
                        &nbsp;•&nbsp;
                        Created: {(exc.get('created_at') or '')[:16]}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:600;">{status_badge}</div>
                    <div style="font-size:0.85rem; opacity:0.6;">
                        {exc['priority']} priority
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action buttons for open exceptions
        if exc["status"] in ("Open", "Investigating"):
            ac1, ac2, ac3 = st.columns(3)

            if exc["status"] == "Open":
                with ac1:
                    if st.button("🔍 Investigate",
                                 key=f"investigate_{exc['exception_id']}"):
                        run_execute(
                            "UPDATE exceptions SET status = 'Investigating' "
                            "WHERE exception_id = ?",
                            (exc["exception_id"],),
                        )
                        st.rerun()

            with ac2:
                if st.button("✅ Resolve",
                             key=f"resolve_{exc['exception_id']}"):
                    st.session_state[f"resolving_{exc['exception_id']}"] = True
                    st.rerun()

            with ac3:
                if st.button("🗑 Close",
                             key=f"close_{exc['exception_id']}"):
                    run_execute(
                        "UPDATE exceptions SET status = 'Closed', "
                        "resolved_at = ? WHERE exception_id = ?",
                        (current_time().isoformat(), exc["exception_id"]),
                    )
                    st.rerun()

            # Resolution form
            if st.session_state.get(f"resolving_{exc['exception_id']}"):
                with st.form(f"resolve_form_{exc['exception_id']}"):
                    resolution = st.text_area(
                        "Resolution Notes",
                        placeholder="Describe how this was resolved...",
                    )
                    new_owner = st.text_input("Resolved by", value=exc.get("owner", ""))

                    if st.form_submit_button("Submit Resolution"):
                        run_execute(
                            "UPDATE exceptions SET status = 'Resolved', "
                            "resolution = ?, resolved_at = ?, owner = ? "
                            "WHERE exception_id = ?",
                            (resolution, current_time().isoformat(),
                             new_owner, exc["exception_id"]),
                        )
                        # If order is in exception status, try to recover
                        order_status = exc.get("order_status")
                        if order_status in ("STOCK_ISSUE", "PICKING_ISSUE",
                                            "PACKING_ISSUE", "COURIER_DELAY", "ON_HOLD"):
                            recovery = {
                                "STOCK_ISSUE": "PROCESSING",
                                "PICKING_ISSUE": "READY_TO_PICK",
                                "PACKING_ISSUE": "PICKING",
                                "COURIER_DELAY": "STAGED",
                                "ON_HOLD": "PROCESSING",
                            }
                            recover_to = recovery.get(order_status, "PROCESSING")
                            # Only recover if no other open exceptions
                            other_open = run_query(
                                "SELECT COUNT(*) AS cnt FROM exceptions "
                                "WHERE order_id = ? AND exception_id != ? "
                                "AND status IN ('Open', 'Investigating')",
                                (exc["order_id"], exc["exception_id"]),
                            )
                            if other_open[0]["cnt"] == 0:
                                run_execute(
                                    "UPDATE orders SET status = ? WHERE order_id = ?",
                                    (recover_to, exc["order_id"]),
                                )

                        st.session_state[f"resolving_{exc['exception_id']}"] = False
                        st.success("Exception resolved!")
                        st.rerun()

        elif exc["status"] == "Resolved" and exc.get("resolution"):
            st.markdown(f"""
            <div style="margin-left:8px; padding:8px 16px; opacity:0.6;
                        border-left:2px solid #22c55e; font-size:0.9rem;">
                ✅ <strong>Resolution:</strong> {exc['resolution']}<br>
                Resolved: {(exc.get('resolved_at') or '')[:16]}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")  # spacer
