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
    """ARR breakdown by status (Won / Lost / Open) with clearer visuals."""
    if COL_ARR not in df.columns:
        return _empty_figure("No ARR data for waterfall")

    won_arr = df.loc[df[COL_IS_CLOSED_WON], COL_ARR].sum()
    lost_arr = df.loc[df[COL_IS_CLOSED_LOST], COL_ARR].sum()
    opn_arr = df.loc[df[COL_IS_OPEN], COL_ARR].sum()
    total = won_arr + lost_arr + opn_arr

    categories = ["Total Pipeline", "Open", "Closed Won", "Closed Lost"]
    values = [total, opn_arr, won_arr, lost_arr]
    colors = ["#455A64", "#1565C0", "#2E7D32", "#C62828"]

    fig = go.Figure(
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f"${v:,.0f}" for v in values],
            textposition="outside",
            hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Pipeline ARR Breakdown by Status",
        yaxis_title="ARR ($)",
        template="plotly_white",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Detail table & stats for Pipeline Coverage
# ---------------------------------------------------------------------------
def pipeline_coverage_stats(df: pd.DataFrame) -> tuple[float, float]:
    """Return (median_open_deal_size, avg_open_deal_size) for open deals."""
    if COL_ARR not in df.columns:
        return 0.0, 0.0
    open_arr = df.loc[df[COL_IS_OPEN], COL_ARR].dropna()
    if open_arr.empty:
        return 0.0, 0.0
    return float(open_arr.median()), float(open_arr.mean())


def pipeline_coverage_detail_table(
    df: pd.DataFrame, target_arr: float, time_col: str
) -> pd.DataFrame | None:
    """Per-period pipeline coverage breakdown."""
    if COL_ARR not in df.columns or time_col not in df.columns:
        return None

    records = []
    for period, grp in df.groupby(time_col, dropna=False):
        open_deals = grp[grp[COL_IS_OPEN]]
        open_arr = open_deals[COL_ARR].sum()
        n_open = len(open_deals)
        median_deal = float(open_deals[COL_ARR].median()) if n_open > 0 else 0
        avg_deal = float(open_deals[COL_ARR].mean()) if n_open > 0 else 0
        coverage = open_arr / target_arr if target_arr > 0 else 0

        records.append({
            "Period": str(period),
            "Open Deals": n_open,
            "Open Pipeline ARR": open_arr,
            "Target ARR": target_arr,
            "Coverage": f"{coverage:.1f}\u00d7",
            "Median Deal": median_deal,
            "Avg Deal": avg_deal,
        })

    return pd.DataFrame(records) if records else None


def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
