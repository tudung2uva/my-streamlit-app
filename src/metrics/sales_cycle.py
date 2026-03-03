"""
Sales Cycle metric.
Formula from pars.md:
  DATEDIF(Deal Creation Date, Deal Close Date, "d")  — won deals only.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import COL_DAYS_TO_CLOSE, COL_IS_CLOSED_WON, COL_DEAL_OWNER, COL_DEAL_TYPE


def avg_sales_cycle_kpi(df: pd.DataFrame) -> float | None:
    """Average sales cycle in days for won deals."""
    if COL_DAYS_TO_CLOSE not in df.columns:
        return None
    won = df.loc[df[COL_IS_CLOSED_WON], COL_DAYS_TO_CLOSE].dropna()
    return float(won.mean()) if not won.empty else None


def median_sales_cycle_kpi(df: pd.DataFrame) -> float | None:
    """Median sales cycle in days for won deals."""
    if COL_DAYS_TO_CLOSE not in df.columns:
        return None
    won = df.loc[df[COL_IS_CLOSED_WON], COL_DAYS_TO_CLOSE].dropna()
    return float(won.median()) if not won.empty else None


def sales_cycle_histogram(df: pd.DataFrame) -> go.Figure:
    """Histogram of days-to-close for won deals."""
    if COL_DAYS_TO_CLOSE not in df.columns:
        return _empty_figure("No close-date data for Sales Cycle")

    won = df.loc[df[COL_IS_CLOSED_WON]].dropna(subset=[COL_DAYS_TO_CLOSE])
    if won.empty:
        return _empty_figure("No won deals in filtered data")

    fig = px.histogram(
        won,
        x=COL_DAYS_TO_CLOSE,
        nbins=20,
        title="Sales Cycle Distribution (Won Deals)",
        labels={COL_DAYS_TO_CLOSE: "Days to Close"},
        color_discrete_sequence=["#1E88E5"],
    )
    fig.update_layout(
        template="plotly_white",
        yaxis_title="Number of Deals",
        bargap=0.05,
    )
    return fig


def sales_cycle_by_dimension(df: pd.DataFrame, group_col: str, label: str) -> go.Figure:
    """Box plot of sales cycle grouped by a dimension (e.g. Deal Owner, Deal Type)."""
    if COL_DAYS_TO_CLOSE not in df.columns or group_col not in df.columns:
        return _empty_figure(f"No data for Sales Cycle by {label}")

    won = df.loc[df[COL_IS_CLOSED_WON]].dropna(subset=[COL_DAYS_TO_CLOSE])
    if won.empty:
        return _empty_figure("No won deals in filtered data")

    fig = px.box(
        won,
        x=group_col,
        y=COL_DAYS_TO_CLOSE,
        title=f"Sales Cycle by {label}",
        labels={COL_DAYS_TO_CLOSE: "Days to Close", group_col: label},
        color=group_col,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(template="plotly_white", showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# Detail table
# ---------------------------------------------------------------------------
def sales_cycle_detail_table(df: pd.DataFrame, time_col: str) -> pd.DataFrame | None:
    """Per-period sales cycle breakdown (won deals only)."""
    if COL_DAYS_TO_CLOSE not in df.columns or time_col not in df.columns:
        return None

    won = df.loc[df[COL_IS_CLOSED_WON]].dropna(subset=[COL_DAYS_TO_CLOSE])
    if won.empty:
        return None

    records = []
    for period, grp in won.groupby(time_col, dropna=False):
        days = grp[COL_DAYS_TO_CLOSE]
        records.append({
            "Period": str(period),
            "Won Deals": len(grp),
            "Avg Days": round(float(days.mean()), 1),
            "Median Days": round(float(days.median()), 1),
            "Min Days": int(days.min()),
            "Max Days": int(days.max()),
        })

    return pd.DataFrame(records) if records else None


def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
