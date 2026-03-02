"""
Reason Lost analysis.
Breakdown of lost deals by Reason Lost — count and ARR.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import COL_ARR, COL_IS_CLOSED_LOST, COL_REASON_LOST


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------
def reason_lost_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of lost deal count by Reason Lost."""
    if COL_REASON_LOST not in df.columns or COL_IS_CLOSED_LOST not in df.columns:
        return _empty_figure("No Reason Lost data")

    lost = df[df[COL_IS_CLOSED_LOST]].copy()
    if lost.empty:
        return _empty_figure("No lost deals in filtered data")

    lost[COL_REASON_LOST] = lost[COL_REASON_LOST].fillna("(Not specified)")

    grouped = (
        lost.groupby(COL_REASON_LOST)
        .size()
        .reset_index(name="Deal Count")
        .sort_values("Deal Count", ascending=True)
    )

    fig = px.bar(
        grouped,
        y=COL_REASON_LOST,
        x="Deal Count",
        orientation="h",
        title="Lost Deals by Reason",
        labels={COL_REASON_LOST: "Reason Lost", "Deal Count": "# Deals"},
        color_discrete_sequence=["#E53935"],
    )
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        height=max(350, len(grouped) * 30 + 100),
    )
    return fig


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------
def reason_lost_table(df: pd.DataFrame) -> pd.DataFrame | None:
    """Tabular breakdown: Reason Lost → Count, ARR Lost, % of Total Lost ARR."""
    if COL_REASON_LOST not in df.columns or COL_IS_CLOSED_LOST not in df.columns:
        return None

    lost = df[df[COL_IS_CLOSED_LOST]].copy()
    if lost.empty:
        return None

    lost[COL_REASON_LOST] = lost[COL_REASON_LOST].fillna("(Not specified)")

    has_arr = COL_ARR in lost.columns

    if has_arr:
        grouped = (
            lost.groupby(COL_REASON_LOST)
            .agg(Deal_Count=(COL_REASON_LOST, "size"), ARR_Lost=(COL_ARR, "sum"))
            .reset_index()
        )
        total_arr = grouped["ARR_Lost"].sum()
        grouped["% of Total"] = (
            (grouped["ARR_Lost"] / total_arr * 100).round(1) if total_arr > 0 else 0
        )
        grouped = grouped.sort_values("ARR_Lost", ascending=False)
        grouped.columns = [COL_REASON_LOST, "Deal Count", "ARR Lost", "% of Total"]
    else:
        grouped = (
            lost.groupby(COL_REASON_LOST)
            .size()
            .reset_index(name="Deal Count")
            .sort_values("Deal Count", ascending=False)
        )

    return grouped


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
