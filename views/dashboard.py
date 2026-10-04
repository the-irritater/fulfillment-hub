"""
Dashboard page — Operations overview.

Designed as an ACTION dashboard, not a chart gallery.
Shows what needs attention RIGHT NOW.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.fulfillment import get_today_summary, get_orders_needing_attention
from utils.priority import risk_emoji, deadline_display, current_time
from utils.db import run_query


def render():
    now = current_time()
    st.markdown(f"""
    <div class="hub-header">Operations Dashboard</div>
    <div class="hub-subtitle">
        📅 {now.strftime('%A, %B %d, %Y')} &nbsp;•&nbsp; 🕐 {now.strftime('%I:%M %p')}
        &nbsp;•&nbsp; What needs your attention right now?
    </div>
    """, unsafe_allow_html=True)

    summary = get_today_summary()

    # ------------------------------------------------------------------
    # Row 1: Key metrics
    # ------------------------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Today's Orders", summary["total"])
    c2.metric("🔴 Priority Orders", summary["priority_orders"])
    at_risk_orders = get_orders_needing_attention(limit=999)
    urgent_count = sum(1 for o in at_risk_orders if o["risk"] == "URGENT")
    c3.metric("⚡ Urgent", urgent_count)
    at_risk_count = sum(1 for o in at_risk_orders if o["risk"] == "AT RISK")
    c4.metric("🟠 At Risk", at_risk_count)
    c5.metric("⚠️ Open Exceptions", summary["open_exceptions"])

    st.markdown("")

    # ------------------------------------------------------------------
    # Row 2: Pipeline status
    # ------------------------------------------------------------------
    st.markdown("#### 📊 Fulfillment Pipeline")
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("Ready to Pick", summary.get("ready_to_pick", 0))
    p2.metric("Picking", summary.get("picking", 0))
    p3.metric("Packed", summary.get("packed", 0))
    p4.metric("Staged", summary.get("staged", 0))
    p5.metric("Shipped", summary.get("shipped", 0))
    p6.metric("Delivered", summary.get("delivered", 0))

    st.markdown("")

    # ------------------------------------------------------------------
    # Row 3: Blockers
    # ------------------------------------------------------------------
    st.markdown("#### 🚫 Blockers")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Stock Issues", summary.get("stock_issues", 0))
    b2.metric("Picking Issues", summary.get("picking_issues", 0))
    b3.metric("Courier Delays", summary.get("courier_delays", 0))
    b4.metric("On Hold", summary.get("on_hold", 0))

    st.markdown("---")

    # ------------------------------------------------------------------
    # Orders needing attention (the CORE feature)
    # ------------------------------------------------------------------
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### 🎯 Orders Needing Attention")
        attention_orders = get_orders_needing_attention(limit=15)

        if not attention_orders:
            st.success("✅ All orders are on track!")
        else:
            for o in attention_orders:
                emoji = risk_emoji(o["risk"])
                dl = deadline_display(o["ship_by"])
                css_class = {
                    "URGENT": "exc-high",
                    "AT RISK": "exc-medium",
                    "ON TRACK": "exc-low",
                }.get(o["risk"], "exc-low")

                status_display = o["status"].replace("_", " ")
                reason_parts = []
                if o["status"] in ("STOCK_ISSUE", "ON_HOLD", "PICKING_ISSUE",
                                   "PACKING_ISSUE", "COURIER_DELAY"):
                    reason_parts.append(status_display)
                if o["exc_count"] > 0:
                    reason_parts.append(f"{o['exc_count']} exception(s)")
                reason = " • ".join(reason_parts) if reason_parts else status_display

                st.markdown(f"""
                <div class="{css_class}">
                    <span style="font-size:1.1rem; font-weight:700;">
                        {emoji} {o['order_id']}
                    </span>
                    &nbsp;&nbsp;
                    <span style="opacity:0.7;">{o['priority']}</span>
                    &nbsp;•&nbsp;
                    <span style="font-weight:500;">{reason}</span>
                    &nbsp;•&nbsp;
                    <span>{dl}</span>
                    &nbsp;&nbsp;
                    <span style="float:right; opacity:0.5;">
                        Score: {o['score']}
                    </span>
                </div>
                """, unsafe_allow_html=True)

    with col_right:
        st.markdown("#### 📈 Order Status Distribution")
        today = current_time().strftime("%Y-%m-%d")
        status_data = run_query(
            "SELECT status, COUNT(*) AS count FROM orders "
            "WHERE order_date = ? GROUP BY status ORDER BY count DESC",
            (today,),
        )
        if status_data:
            df = pd.DataFrame(status_data)
            colors = {
                "DELIVERED": "#22c55e", "SHIPPED": "#3b82f6",
                "STAGED": "#6366f1", "PACKED": "#8b5cf6",
                "PICKING": "#a78bfa", "READY_TO_PICK": "#c4b5fd",
                "PROCESSING": "#e2e8f0", "NEW": "#94a3b8",
                "STOCK_ISSUE": "#ef4444", "PICKING_ISSUE": "#f97316",
                "ON_HOLD": "#fbbf24", "COURIER_DELAY": "#fb923c",
                "PACKING_ISSUE": "#f43f5e", "CANCELLED": "#6b7280",
            }
            df["color"] = df["status"].map(colors).fillna("#64748b")
            fig = px.pie(
                df, values="count", names="status",
                color="status",
                color_discrete_map=colors,
                hole=0.55,
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#fafafa", family="Inter"),
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(font=dict(size=10)),
                height=350,
            )
            fig.update_traces(textposition="inside", textinfo="value")
            st.plotly_chart(fig, use_container_width=True)

        # Channel mix
        st.markdown("#### 🏪 Channel Mix")
        channel_data = run_query(
            "SELECT channel, COUNT(*) AS count FROM orders "
            "WHERE order_date = ? GROUP BY channel ORDER BY count DESC",
            (today,),
        )
        if channel_data:
            df_ch = pd.DataFrame(channel_data)
            fig2 = px.bar(
                df_ch, x="channel", y="count",
                color="channel",
                color_discrete_sequence=["#6C63FF", "#a78bfa", "#c4b5fd",
                                         "#e9d5ff", "#f3e8ff"],
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#fafafa", family="Inter"),
                margin=dict(t=20, b=40, l=40, r=20),
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(108,99,255,0.1)"),
                height=250,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ------------------------------------------------------------------
    # Courier pickup timeline
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### 🚚 Courier Pickup Windows")
    couriers = run_query("SELECT * FROM couriers WHERE is_active = 1 ORDER BY pickup_time")
    if couriers:
        cols = st.columns(len(couriers))
        for i, c in enumerate(couriers):
            with cols[i]:
                # Count staged orders for this courier
                staged = run_query(
                    "SELECT COUNT(*) AS cnt FROM orders "
                    "WHERE courier_id = ? AND status = 'STAGED' AND order_date = ?",
                    (c["courier_id"], today),
                )
                cnt = staged[0]["cnt"] if staged else 0
                pickup_str = c["pickup_time"]
                try:
                    ph, pm = map(int, pickup_str.split(":"))
                    pickup_dt = current_time().replace(hour=ph, minute=pm)
                    remaining = pickup_dt - current_time()
                    if remaining.total_seconds() < 0:
                        time_label = "✅ Picked up"
                    elif remaining.total_seconds() < 3600:
                        time_label = f"🔴 {int(remaining.total_seconds()//60)} min"
                    else:
                        time_label = f"🟢 {int(remaining.total_seconds()//3600)}h"
                except Exception:
                    time_label = pickup_str

                st.markdown(f"""
                <div class="hub-card" style="text-align:center;">
                    <div style="font-weight:700; font-size:1.1rem;">{c['courier_name']}</div>
                    <div style="font-size:0.85rem; opacity:0.6;">Pickup: {pickup_str}</div>
                    <div style="font-size:1.4rem; font-weight:700; margin:8px 0;">
                        {time_label}
                    </div>
                    <div style="opacity:0.7;">{cnt} orders staged</div>
                    <div style="font-size:0.8rem; opacity:0.5;">
                        ₹{c['cost_per_order']} • {c['delivery_days']}d delivery
                    </div>
                </div>
                """, unsafe_allow_html=True)
