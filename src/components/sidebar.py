"""
Sidebar filter component.
Dynamically renders single-select and multi-select filters based on
available columns in the uploaded data. Returns filtered DataFrame.
Includes Currency selector, Fiscal Year Start, and data filters.
"""

import pandas as pd
import streamlit as st

from utils.constants import (
    COL_DEAL_STAGE,
    COL_FISCAL_MONTH,
    COL_FISCAL_QUARTER,
    COL_FISCAL_WEEK,
    COL_FISCAL_YEAR,
    FILTER_CONFIG,
)
from utils.helpers import add_derived_columns

# Map the time increment label to the derived column
TIME_INCREMENT_MAP = {
    "Year": COL_FISCAL_YEAR,
    "Quarter": COL_FISCAL_QUARTER,
    "Month": COL_FISCAL_MONTH,
    "Week": COL_FISCAL_WEEK,
}

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def render_sidebar(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """
    Render sidebar filters and return (filtered_df, time_column).
    time_column is the derived column name matching the selected time increment.
    """
    available = st.session_state.get("available_columns", set())

    st.sidebar.header("Filters")

    # Reset button
    if st.sidebar.button("🔄 Reset All Filters"):
        for key in list(st.session_state.keys()):
            if key.startswith("filter_"):
                del st.session_state[key]
        st.rerun()

    # ----- Currency selector -----
    currency_options = ["€", "$", "£"]
    currency = st.sidebar.selectbox(
        "Currency",
        options=currency_options,
        index=0,
        key="filter_currency",
        help="Display currency symbol (does not convert values)",
    )
    st.session_state["currency"] = currency

    # ----- Fiscal Year Start -----
    fy_month = st.sidebar.selectbox(
        "Fiscal Year Start",
        options=MONTH_NAMES,
        index=0,
        key="filter_fy_start",
        help="First month of the fiscal year. Affects Year/Quarter grouping.",
    )
    fy_start_month = MONTH_NAMES.index(fy_month) + 1

    # Re-derive fiscal columns if FY start changed
    prev_fy = st.session_state.get("_fy_start_month", 1)
    if fy_start_month != prev_fy and COL_DEAL_STAGE in df.columns:
        df = add_derived_columns(df, fy_start_month=fy_start_month)
        st.session_state["df"] = df
        st.session_state["_fy_start_month"] = fy_start_month

    st.sidebar.markdown("---")

    time_col = COL_FISCAL_QUARTER  # default
    filtered = df.copy()

    for fconf in FILTER_CONFIG:
        fkey = f"filter_{fconf['key']}"

        # --- Time Increment (single select, always shown) ---
        if fconf["key"] == "time_increment":
            selected = st.sidebar.selectbox(
                fconf["label"],
                options=fconf["options"],
                index=fconf["options"].index(fconf["default"]),
                key=fkey,
            )
            time_col = TIME_INCREMENT_MAP.get(selected, COL_FISCAL_QUARTER)
            continue

        # --- Multi-select filters ---
        # Skip if the source column isn't available
        depends_col = fconf.get("depends_on")
        if depends_col and depends_col not in available and fconf["column"] not in df.columns:
            continue

        col = fconf["column"]
        if col not in df.columns:
            continue

        unique_vals = sorted(df[col].dropna().unique().astype(str).tolist())
        if not unique_vals:
            continue

        selected_vals = st.sidebar.multiselect(
            fconf["label"],
            options=unique_vals,
            default=[],
            key=fkey,
        )

        if selected_vals:
            filtered = filtered[filtered[col].astype(str).isin(selected_vals)]

    # Show filtered count
    st.sidebar.markdown("---")
    st.sidebar.metric("Deals shown", f"{len(filtered):,}", delta=None)

    return filtered, time_col
