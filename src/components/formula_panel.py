"""
Formula Inspector panel.
Shows metric definitions and a per-period computation table for the
currently filtered data. Ported from render.js buildFormulaPanel().
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.constants import (
    COL_ARR,
    COL_DEAL_TYPE,
    COL_IS_CLOSED_LOST,
    COL_IS_CLOSED_WON,
    COL_IS_OPEN,
    COL_DAYS_TO_CLOSE,
    COL_REASON_LOST,
)

# ---------------------------------------------------------------------------
# Metric definitions (priority chain: render.js > Handbook > pars.md)
# ---------------------------------------------------------------------------
FORMULA_DEFINITIONS = [
    {
        "metric": "Count Win Rate",
        "formula": "Won Deals / (Won + Lost + Open)",
        "notes": "Cohort by Deal Creation Date. All deals in the cohort counted.",
    },
    {
        "metric": "Revenue Win Rate",
        "formula": "ARR Won / (ARR Won + ARR Lost + ARR Open)",
        "notes": "Same cohort logic, weighted by ARR Amount.",
    },
    {
        "metric": "Pipeline Coverage",
        "formula": "Open Pipeline ARR / Target ARR",
        "notes": "Open = Deal Stage ≠ Closed Won / Closed Lost. Target ARR configured in sidebar.",
    },
    {
        "metric": "Sales Cycle",
        "formula": "DATEDIF(Deal Creation Date, Deal Close Date, 'd')",
        "notes": "Won deals only. Avg and Median reported.",
    },
    {
        "metric": "Expansion ARR",
        "formula": "SUM(ARR) where Deal Type IN (Upsell, Cross-sell) — won deals",
        "notes": "Requires Deal Type and ARR Amount columns.",
    },
    {
        "metric": "Pipeline Production",
        "formula": "SUM(ARR) for deals created in the selected period",
        "notes": "All deal stages included (measures new pipeline generated).",
    },
    {
        "metric": "Concentration",
        "formula": "ARR share (%) per dimension group",
        "notes": "#1%, Top 3%, Top 10% thresholds. ≥30% #1 or ≥60% Top 3 = Concentrated.",
    },
    {
        "metric": "ACV (Avg Contract Value)",
        "formula": "SUM(ARR Won) / COUNT(Won Deals)",
        "notes": "Closed Won deals only. Per-period avg and median reported.",
    },
    {
        "metric": "Net Revenue Retention",
        "formula": "(Starting ARR + Expansion − Churn) / Starting ARR",
        "notes": "Expansion = won Upsell/Cross-sell ARR. Churn = Churn ARR column. De-duped by customer.",
    },
    {
        "metric": "Logo Churn",
        "formula": "Churned Customers / Starting Customers",
        "notes": "Churned = non-null Churn Date. Starting = ARR per 1/1 > 0. De-duped by customer.",
    },
    {
        "metric": "ARR Churn",
        "formula": "SUM(Churn ARR) / SUM(Starting ARR)",
        "notes": "Both numerator and denominator de-duplicated by Customer Name.",
    },
]


def render_formula_panel(df: pd.DataFrame, time_col: str) -> None:
    """Render the Formula Inspector inside an expander."""
    with st.expander("📐 Formula Definitions & Computation Detail", expanded=False):
        # --- Definitions table ---
        st.markdown("#### Metric Definitions")
        def_df = pd.DataFrame(FORMULA_DEFINITIONS)
        st.dataframe(def_df, use_container_width=True, hide_index=True)

        # --- Per-period computation table ---
        if time_col in df.columns and COL_IS_CLOSED_WON in df.columns:
            st.markdown("#### Per-Period Computation")
            records = []
            for period, grp in df.groupby(time_col, dropna=False):
                won = int(grp[COL_IS_CLOSED_WON].sum())
                lost = int(grp[COL_IS_CLOSED_LOST].sum()) if COL_IS_CLOSED_LOST in grp.columns else 0
                opn = int(grp[COL_IS_OPEN].sum()) if COL_IS_OPEN in grp.columns else 0
                total = won + lost + opn

                arr_won = grp.loc[grp[COL_IS_CLOSED_WON], COL_ARR].sum() if COL_ARR in grp.columns else 0
                arr_lost = grp.loc[grp[COL_IS_CLOSED_LOST], COL_ARR].sum() if COL_ARR in grp.columns and COL_IS_CLOSED_LOST in grp.columns else 0
                arr_open = grp.loc[grp[COL_IS_OPEN], COL_ARR].sum() if COL_ARR in grp.columns and COL_IS_OPEN in grp.columns else 0
                arr_total = arr_won + arr_lost + arr_open

                count_wr = won / total if total > 0 else 0
                rev_wr = arr_won / arr_total if arr_total > 0 else 0

                cycle_days = grp.loc[grp[COL_IS_CLOSED_WON], COL_DAYS_TO_CLOSE].dropna() if COL_DAYS_TO_CLOSE in grp.columns else pd.Series(dtype=float)
                avg_cycle = float(cycle_days.mean()) if not cycle_days.empty else None

                median_cycle = float(cycle_days.median()) if not cycle_days.empty else None
                acv = arr_won / won if won > 0 else 0

                records.append({
                    "Period": str(period),
                    "Won": won,
                    "Lost": lost,
                    "Open": opn,
                    "Count WR": f"{count_wr:.1%}",
                    "ARR Won": f"${arr_won:,.0f}",
                    "ARR Total": f"${arr_total:,.0f}",
                    "Rev WR": f"{rev_wr:.1%}",
                    "ACV": f"${acv:,.0f}",
                    "Avg Cycle (d)": f"{avg_cycle:.0f}" if avg_cycle is not None else "—",
                    "Med Cycle (d)": f"{median_cycle:.0f}" if median_cycle is not None else "—",
                })

            if records:
                comp_df = pd.DataFrame(records)
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
