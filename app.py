"""
Fulfillment Hub — Main Application Entry Point

Simple Warehouse & Order Fulfillment Operations System.
"""

import streamlit as st
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from database.seed_data import seed, DB_PATH

# Auto-seed database if it doesn't exist
if not os.path.exists(DB_PATH):
    seed()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Fulfillment Hub",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---------- Global ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit footer and menu */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
    border-right: 1px solid rgba(108, 99, 255, 0.2);
}

[data-testid="stSidebar"] .stRadio label {
    font-size: 1.05rem;
    padding: 0.35rem 0;
}

/* ---------- Metric cards ---------- */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(108,99,255,0.12) 0%, rgba(108,99,255,0.04) 100%);
    border: 1px solid rgba(108,99,255,0.2);
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #6C63FF, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

[data-testid="stMetricLabel"] {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.75;
}

/* ---------- Buttons ---------- */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    border: 1px solid rgba(108,99,255,0.4);
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: #6C63FF;
    box-shadow: 0 0 15px rgba(108,99,255,0.3);
    transform: translateY(-1px);
}

/* ---------- Data frames / tables ---------- */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(108,99,255,0.15);
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
}

/* ---------- Alerts / status badges ---------- */
.status-urgent {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    padding: 4px 12px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    display: inline-block;
}
.status-at-risk {
    background: rgba(251, 146, 60, 0.15);
    color: #fb923c;
    padding: 4px 12px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    display: inline-block;
}
.status-on-track {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
    padding: 4px 12px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    display: inline-block;
}

/* ---------- Cards ---------- */
.hub-card {
    background: linear-gradient(135deg, rgba(26,29,41,0.9) 0%, rgba(14,17,23,0.9) 100%);
    border: 1px solid rgba(108,99,255,0.2);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}

/* ---------- Header ---------- */
.hub-header {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6C63FF 0%, #a78bfa 50%, #c4b5fd 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.hub-subtitle {
    color: rgba(250,250,250,0.55);
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* ---------- Picking card ---------- */
.pick-item {
    background: rgba(108,99,255,0.08);
    border: 1px solid rgba(108,99,255,0.2);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
}
.pick-sku {
    font-size: 1.3rem;
    font-weight: 700;
    color: #a78bfa;
}
.pick-product {
    font-size: 1.05rem;
    color: rgba(250,250,250,0.8);
}
.pick-location {
    font-size: 1.1rem;
    font-weight: 600;
    color: #6C63FF;
    margin-top: 4px;
}

/* ---------- Status stepper ---------- */
.step-done { color: #22c55e; font-weight: 600; }
.step-current { color: #6C63FF; font-weight: 700; font-size: 1.05em; }
.step-pending { color: rgba(250,250,250,0.35); }

/* ---------- Exception card ---------- */
.exc-high {
    border-left: 4px solid #ef4444;
    background: rgba(239,68,68,0.06);
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.exc-medium {
    border-left: 4px solid #fb923c;
    background: rgba(251,146,60,0.06);
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.exc-low {
    border-left: 4px solid #22c55e;
    background: rgba(34,197,94,0.06);
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="hub-header">📦 Fulfillment Hub</div>', unsafe_allow_html=True)
    st.markdown('<div class="hub-subtitle">Warehouse Operations Control Center</div>',
                unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "🏠  Dashboard",
            "📋  Orders",
            "📦  Inventory",
            "🛒  Picking & Packing",
            "⚠️  Exceptions",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Fulfillment Hub v1.0")
    st.caption("XYZ Operations System")

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
if "Dashboard" in page:
    from pages.dashboard import render
    render()
elif "Orders" in page:
    from pages.orders import render
    render()
elif "Inventory" in page:
    from pages.inventory import render
    render()
elif "Picking" in page:
    from pages.picking import render
    render()
elif "Exceptions" in page:
    from pages.exceptions import render
    render()
