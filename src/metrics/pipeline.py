"""
Pipeline Coverage metric.
Formula from pars.md:
  Open Pipeline ARR / Target ARR
  Open = Deal Stage NOT IN ('Closed Won', 'Closed Lost')
  Target ARR defaults to $1 M if not provided.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import (
    COL_ARR,
    COL_DEAL_STAGE,
    COL_IS_CLOSED_LOST,
    COL_IS_CLOSED_WON,
    COL_IS_OPEN,
    STAGE_CLOSED_LOST,
    STAGE_CLOSED_WON,
)


def pipeline_coverage_kpi(df: pd.DataFrame, target_arr: float = 1_000_000) -> float:
    """Open Pipeline ARR / Target ARR — returns ratio (e.g. 2.5 = 2.5×)."""
    if COL_ARR not in df.columns:
        return 0
    open_arr = df.loc[df[COL_IS_OPEN], COL_ARR].sum()
    return open_arr / target_arr if target_arr > 0 else 0


def open_pipeline_arr(df: pd.DataFrame) -> float:
    """Total ARR for open deals."""
    if COL_ARR not in df.columns:
        return 0
    return float(df.loc[df[COL_IS_OPEN], COL_ARR].sum())


def pipeline_by_stage_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of ARR grouped by Deal Stage (open deals only)."""
    if COL_ARR not in df.columns or COL_DEAL_STAGE not in df.columns:
        return _empty_figure("No data for Pipeline by Stage")

    open_df = df[df[COL_IS_OPEN]].copy()
    if open_df.empty:
        return _empty_figure("No open deals in filtered data")

    stage_arr = (
        open_df.groupby(COL_DEAL_STAGE)[COL_ARR]
        .sum()
        .reset_index()
        .sort_values(COL_ARR, ascending=True)
    )

    fig = px.bar(
        stage_arr,
        y=COL_DEAL_STAGE,
        x=COL_ARR,
        orientation="h",
        title="Open Pipeline by Deal Stage",
        labels={COL_ARR: "ARR ($)", COL_DEAL_STAGE: "Stage"},
        color=COL_DEAL_STAGE,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        showlegend=False,
        template="plotly_white",
        xaxis_tickprefix="$",
        xaxis_tickformat=",",
    )
    return fig


def pipeline_waterfall_chart(df: pd.DataFrame) -> go.Figure:
    """Waterfall showing Won / Lost / Open ARR splits."""
    if COL_ARR not in df.columns:
        return _empty_figure("No ARR data for waterfall")

    won_arr = df.loc[df[COL_IS_CLOSED_WON], COL_ARR].sum()
    lost_arr = df.loc[df[COL_IS_CLOSED_LOST], COL_ARR].sum()
    opn_arr = df.loc[df[COL_IS_OPEN], COL_ARR].sum()
    total = won_arr + lost_arr + opn_arr

    fig = go.Figure(
        go.Waterfall(
            x=["Total Pipeline", "Closed Won", "Closed Lost", "Open"],
            y=[total, -won_arr, -lost_arr, -opn_arr],
            measure=["absolute", "relative", "relative", "relative"],
            connector=dict(line=dict(color="rgba(0,0,0,0)")),
            decreasing=dict(marker_color="#43A047"),
            increasing=dict(marker_color="#E53935"),
            totals=dict(marker_color="#1E88E5"),
            text=[f"${v:,.0f}" for v in [total, won_arr, lost_arr, opn_arr]],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Pipeline ARR Breakdown",
        yaxis_title="ARR ($)",
        template="plotly_white",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
    )
    return fig


def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
