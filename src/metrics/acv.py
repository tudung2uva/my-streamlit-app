"""
ACV (Average Contract Value) metric.
Formula:
  ACV = SUM(ARR Won) / COUNT(Won Deals)
  Applies to Closed Won deals only.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import COL_ARR, COL_IS_CLOSED_WON


# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------
def acv_kpi(df: pd.DataFrame) -> float:
    """Average Contract Value for won deals."""
    if COL_ARR not in df.columns:
        return 0.0
    won = df.loc[df[COL_IS_CLOSED_WON], COL_ARR].dropna()
    if won.empty:
        return 0.0
    return float(won.mean())


# ---------------------------------------------------------------------------
# Over-time chart
# ---------------------------------------------------------------------------
def acv_over_time_chart(df: pd.DataFrame, time_col: str) -> go.Figure:
    """Bar chart of ACV per period (won deals only)."""
    if COL_ARR not in df.columns or time_col not in df.columns:
        return _empty_figure("No data for ACV over time")

    won = df.loc[df[COL_IS_CLOSED_WON]].dropna(subset=[COL_ARR])
    if won.empty:
        return _empty_figure("No won deals in filtered data")

    grouped = (
        won.groupby(time_col, dropna=False)[COL_ARR]
        .agg(["mean", "count", "sum"])
        .reset_index()
        .rename(columns={"mean": "ACV", "count": "Won Deals", "sum": "Total ARR Won"})
        .sort_values(time_col)
    )

    fig = px.bar(
        grouped,
        x=time_col,
        y="ACV",
        title="ACV (Average Contract Value) Over Time",
        labels={"ACV": "Average Contract Value", time_col: "Period"},
        color_discrete_sequence=["#1E88E5"],
        text="ACV",
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
    )
    return fig


# ---------------------------------------------------------------------------
# Detail table
# ---------------------------------------------------------------------------
def acv_detail_table(df: pd.DataFrame, time_col: str) -> pd.DataFrame | None:
    """Per-period ACV breakdown table."""
    if COL_ARR not in df.columns or time_col not in df.columns:
        return None

    won = df.loc[df[COL_IS_CLOSED_WON]].dropna(subset=[COL_ARR])
    if won.empty:
        return None

    grouped = (
        won.groupby(time_col, dropna=False)[COL_ARR]
        .agg(["count", "sum", "mean", "median"])
        .reset_index()
        .rename(columns={
            time_col: "Period",
            "count": "Won Deals",
            "sum": "Total ARR Won",
            "mean": "Avg ACV",
            "median": "Median ACV",
        })
        .sort_values("Period")
    )
    grouped.columns = ["Period", "Won Deals", "Total ARR Won", "Avg ACV", "Median ACV"]
    return grouped


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
