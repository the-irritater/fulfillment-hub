"""
Inventory page — Stock levels, availability, and transfer management.
"""

import streamlit as st
import pandas as pd

from utils.inventory import (
    get_inventory_summary, get_pending_transfers, create_transfer,
)
from utils.db import run_query, run_execute


def render():
    st.markdown('<div class="hub-header">📦 Inventory Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="hub-subtitle">Stock levels across warehouses • Availability • Transfers</div>',
                unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 Stock Overview", "🔄 Transfers"])

    # ==================================================================
    # Tab 1: Stock Overview
    # ==================================================================
    with tab1:
        inventory = get_inventory_summary()

        # Summary metrics
        total_skus = len(inventory)
        ok_count = sum(1 for i in inventory if i["stock_status"] == "OK")
        low_count = sum(1 for i in inventory if i["stock_status"] == "LOW")
        transfer_count = sum(1 for i in inventory if i["stock_status"] == "TRANSFER")
        oos_count = sum(1 for i in inventory if i["stock_status"] == "OUT_OF_STOCK")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total SKUs", total_skus)
        m2.metric("✅ In Stock", ok_count)
        m3.metric("⚠️ Low Stock", low_count)
        m4.metric("🔄 Transfer Needed", transfer_count)
        m5.metric("❌ Out of Stock", oos_count)

        st.markdown("")

        # Filters
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        with fc1:
            search = st.text_input("🔍 Search SKU or Product", key="inv_search",
                                   placeholder="TSH-BLK or T-Shirt...")
        with fc2:
            categories = ["All"] + sorted(set(i["category"] for i in inventory if i["category"]))
            cat_filter = st.selectbox("Category", categories)
        with fc3:
            stock_filter = st.selectbox("Stock Status",
                                        ["All", "OK", "LOW", "TRANSFER", "OUT_OF_STOCK"])

        # Filter data
        filtered = inventory
        if search:
            s = search.lower()
            filtered = [i for i in filtered
                        if s in i["sku"].lower() or s in i["product_name"].lower()]
        if cat_filter != "All":
            filtered = [i for i in filtered if i["category"] == cat_filter]
        if stock_filter != "All":
            filtered = [i for i in filtered if i["stock_status"] == stock_filter]

        st.markdown(f"**{len(filtered)} SKUs**")

        # Display as styled cards grouped by status
        if not filtered:
            st.info("No items match the current filters.")
        else:
            # Render table
            df = pd.DataFrame(filtered)
            df = df[["sku", "product_name", "variant", "category",
                      "main_wh", "reserved", "available",
                      "secondary_wh", "main_location", "stock_status"]]
            df.columns = ["SKU", "Product", "Variant", "Category",
                          "Main WH", "Reserved", "Available",
                          "Secondary WH", "Location", "Status"]

            def _color_status(val):
                colors = {
                    "OK": "color: #22c55e",
                    "LOW": "color: #fbbf24",
                    "TRANSFER": "color: #f97316",
                    "OUT_OF_STOCK": "color: #ef4444",
                }
                return colors.get(val, "")

            styled = df.style.map(_color_status, subset=["Status"])
            st.dataframe(styled, use_container_width=True, height=500)

            # ----------------------------------------------------------
            # Transfer needed section
            # ----------------------------------------------------------
            transfer_items = [i for i in filtered if i["stock_status"] == "TRANSFER"]
            if transfer_items:
                st.markdown("---")
                st.markdown("#### 🔄 Transfer Required")
                st.markdown("These SKUs are **out of stock in Main Warehouse** but available in Secondary.")

                for item in transfer_items:
                    css_class = "exc-medium"
                    st.markdown(f"""
                    <div class="{css_class}">
                        <div style="display:flex; justify-content:space-between;">
                            <div>
                                <span class="pick-sku">{item['sku']}</span>
                                <span class="pick-product"> — {item['product_name']} ({item['variant']})</span>
                            </div>
                            <div style="text-align:right;">
                                Main WH: <strong>{item['main_wh']}</strong> &nbsp;•&nbsp;
                                Secondary: <strong>{item['secondary_wh']}</strong>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    tc1, tc2 = st.columns([1, 3])
                    with tc1:
                        qty = st.number_input(
                            "Transfer Qty", min_value=1,
                            max_value=item["secondary_wh"],
                            value=min(5, item["secondary_wh"]),
                            key=f"transfer_qty_{item['sku']}",
                        )
                    with tc2:
                        st.markdown("")  # spacer
                        st.markdown("")
                        if st.button(f"📤 Create Transfer", key=f"transfer_{item['sku']}"):
                            create_transfer(item["sku"], qty)
                            st.success(
                                f"Transfer request created: {qty}× {item['sku']} "
                                f"from Secondary → Main"
                            )
                            st.rerun()

    # ==================================================================
    # Tab 2: Transfers
    # ==================================================================
    with tab2:
        st.markdown("#### Pending & In-Transit Transfers")

        transfers = get_pending_transfers()

        if not transfers:
            st.success("✅ No pending transfers.")
        else:
            for t in transfers:
                status_emoji = "📤" if t["status"] == "REQUESTED" else "🚚"
                css = "exc-medium" if t["status"] == "REQUESTED" else "exc-low"
                st.markdown(f"""
                <div class="{css}">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <span style="font-weight:700;">{status_emoji} Transfer #{t['transfer_id']}</span>
                            &nbsp;•&nbsp;
                            <span class="pick-sku">{t['sku']}</span>
                            &nbsp;—&nbsp;
                            {t['product_name']} ({t['variant']})
                        </div>
                        <div>
                            <strong>{t['quantity']}</strong> units &nbsp;•&nbsp;
                            {t['from_warehouse']} → {t['to_warehouse']} &nbsp;•&nbsp;
                            Status: <strong>{t['status']}</strong>
                        </div>
                    </div>
                    <div style="margin-top:4px; opacity:0.5; font-size:0.85rem;">
                        Requested: {t['requested_at'][:16] if t['requested_at'] else '—'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                tc1, tc2, tc3 = st.columns(3)
                if t["status"] == "REQUESTED":
                    with tc1:
                        if st.button("🚚 Mark In Transit",
                                     key=f"transit_{t['transfer_id']}"):
                            run_execute(
                                "UPDATE transfers SET status = 'IN_TRANSIT' "
                                "WHERE transfer_id = ?",
                                (t["transfer_id"],),
                            )
                            st.rerun()
                if t["status"] in ("REQUESTED", "IN_TRANSIT"):
                    with tc2:
                        if st.button("✅ Complete Transfer",
                                     key=f"complete_{t['transfer_id']}"):
                            # Check stock and double completion
                            from utils.db import run_query, run_transaction
                            
                            # Verify transfer is still eligible
                            curr_t = run_query("SELECT status FROM transfers WHERE transfer_id = ?", (t["transfer_id"],))
                            if not curr_t or curr_t[0]["status"] not in ("REQUESTED", "IN_TRANSIT"):
                                st.error("❌ Transfer is no longer active.")
                            else:
                                src_inv = run_query("SELECT quantity, reserved FROM inventory WHERE sku = ? AND warehouse = ?", (t["sku"], t["from_warehouse"]))
                                if not src_inv or (src_inv[0]["quantity"] - src_inv[0]["reserved"]) < t["quantity"]:
                                    st.error(f"❌ Insufficient available stock in {t['from_warehouse']} warehouse to complete transfer.")
                                else:
                                    # Ensure destination inventory record exists
                                    dst_inv = run_query("SELECT * FROM inventory WHERE sku = ? AND warehouse = ?", (t["sku"], t["to_warehouse"]))
                                    queries = []
                                    if not dst_inv:
                                        queries.append((
                                            "INSERT INTO inventory (sku, warehouse, quantity, reserved, min_threshold) VALUES (?, ?, 0, 0, 5)",
                                            (t["sku"], t["to_warehouse"])
                                        ))
                                        
                                    from utils.priority import current_time
                                    queries.extend([
                                        (
                                            "UPDATE transfers SET status = 'COMPLETED', completed_at = ? WHERE transfer_id = ?",
                                            (current_time().isoformat(), t["transfer_id"])
                                        ),
                                        (
                                            "UPDATE inventory SET quantity = quantity - ? WHERE sku = ? AND warehouse = ?",
                                            (t["quantity"], t["sku"], t["from_warehouse"])
                                        ),
                                        (
                                            "UPDATE inventory SET quantity = quantity + ? WHERE sku = ? AND warehouse = ?",
                                            (t["quantity"], t["sku"], t["to_warehouse"])
                                        )
                                    ])
                                    try:
                                        run_transaction(queries)
                                        st.success(f"Transfer #{t['transfer_id']} completed!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to complete transfer: {e}")
                    with tc3:
                        if st.button("❌ Cancel",
                                     key=f"cancel_{t['transfer_id']}"):
                            run_execute(
                                "UPDATE transfers SET status = 'CANCELLED' "
                                "WHERE transfer_id = ?",
                                (t["transfer_id"],),
                            )
                            st.rerun()
