"""
Expansion ARR metric.
Formula from pars.md:
  SUMIFS(ARR Amount, Deal Type, "Upsell") + SUMIFS(ARR Amount, Deal Type, "Cross-sell")
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import COL_ARR, COL_DEAL_TYPE, COL_IS_CLOSED_WON


# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------
_EXPANSION_TYPES = {"upsell", "cross-sell", "cross sell", "crosssell"}


def expansion_arr_kpi(df: pd.DataFrame) -> float:
    """Total Expansion ARR = sum of ARR for Upsell + Cross-sell deals (won only)."""
    if COL_ARR not in df.columns or COL_DEAL_TYPE not in df.columns:
        return 0.0
    mask = (
        df[COL_DEAL_TYPE].astype(str).str.strip().str.lower().isin(_EXPANSION_TYPES)
        & df[COL_IS_CLOSED_WON]
    )
    return float(df.loc[mask, COL_ARR].sum())


# ---------------------------------------------------------------------------
# Over-time chart
# ---------------------------------------------------------------------------
def expansion_over_time_chart(df: pd.DataFrame, time_col: str) -> go.Figure:
    """Stacked bar of Upsell vs Cross-sell ARR per period (won deals)."""
    if COL_ARR not in df.columns or COL_DEAL_TYPE not in df.columns:
        return _empty_figure("No data for Expansion ARR")

    exp = df[
        df[COL_DEAL_TYPE].astype(str).str.strip().str.lower().isin(_EXPANSION_TYPES)
        & df[COL_IS_CLOSED_WON]
    ].copy()

    if exp.empty or time_col not in exp.columns:
        return _empty_figure("No expansion deals in filtered data")

    # Normalise type label for display
    exp["_type"] = exp[COL_DEAL_TYPE].astype(str).str.strip().str.title()

    grouped = (
        exp.groupby([time_col, "_type"], dropna=False)[COL_ARR]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        grouped,
        x=time_col,
        y=COL_ARR,
        color="_type",
        title="Expansion ARR Over Time (Won Deals)",
        labels={COL_ARR: "ARR", time_col: "Period", "_type": "Deal Type"},
        color_discrete_sequence=["#43A047", "#1E88E5"],
        barmode="stack",
    )
    fig.update_layout(
        template="plotly_white",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
