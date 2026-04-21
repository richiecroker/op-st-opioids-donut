import streamlit as st
import pandas as pd
from datetime import datetime
import yaml
import os
from db import get_duckdb_connection, get_latest_dates

# ── Page config — must be first Streamlit command ─────────────────────────────

st.set_page_config(layout="wide")

# ── Cached data loaders ────────────────────────────────────────────────────────

@st.cache_data
def load_vmpp_df(_conn):
    return _conn.execute("SELECT * FROM prescribing").df()

@st.cache_data
def load_practices_df(_conn):
    return _conn.execute("SELECT * FROM practices").df()

# ── Helper / formatting functions ─────────────────────────────────────────────

def cascading_filter(df, col, label, key):
    opts = sorted(df[col].dropna().unique().tolist())
    sel = [v for v in st.session_state.get(key, []) if v in opts]
    sel = st.multiselect(label, opts, default=sel, key=key)
    return df if not sel else df[df[col].isin(sel)]

# ── App ────────────────────────────────────────────────────────────────────────

# --- Load data ---
conn = get_duckdb_connection()
practices_df = load_practices_df(conn)

dates = get_latest_dates()
max_rx_date = dates["prescribing"]
rx_month = datetime.strptime(max_rx_date, '%Y-%m-%d').strftime('%B %Y')

# --- Header ---
base_dir = os.path.dirname(__file__)
st.image(os.path.join(base_dir, "content", "OpenPrescribing.svg"))
st.info(
    """##### Hello!  This is a **very** early prototype of estimating the impact of a possible visualation to be used in OpenPrescribing, showing opioid prescribing.  
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)"""
)

# --- Sidebar filters ---
with st.sidebar:
    st.markdown(f"### Prescribing data used for estimate: {rx_month}")

    st.header("Organisation Filter")
    st.info("Select an organisation at any level.")

    df_region   = cascading_filter(practices_df, "region_name",   "Region",   "sel_region")
    df_icb      = cascading_filter(df_region,    "icb_name",      "ICB",      "sel_icb")
    df_pcn      = cascading_filter(df_icb,       "pcn_name",      "PCN",      "sel_pcn")
    df_selected = cascading_filter(df_pcn,       "practice_name", "Practice", "sel_practice")

    selected_practice_codes = df_selected["practice_code"].unique().tolist()

    st.header("Tariff Filter")
    sel_tariff_cat = st.multiselect(
        "DT Category",
        ["(All)"] + sorted(tariff_cat_opts),
        key="sel_tariff_cat",
    )

    sort_option = st.radio(
        "Sort by",
        ["Largest Increases", "Largest Reductions"],
        key="sort_option",
    )
