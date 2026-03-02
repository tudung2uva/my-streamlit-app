"""
Pipeline Production metric.
Formula from pars.md:
  SUMIFS(ARR Amount, Deal Creation Date >= Start, Deal Creation Date <= End)
  Total ARR of deals *created* in the selected period, regardless of stage.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import COL_ARR


# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------
def pipeline_production_kpi(df: pd.DataFrame) -> float:
    """Total new pipeline ARR produced in the filtered data set."""
    if COL_ARR not in df.columns:
        return 0.0
    return float(df[COL_ARR].sum())


# ---------------------------------------------------------------------------
# Over-time chart
# ---------------------------------------------------------------------------
def pipeline_production_chart(df: pd.DataFrame, time_col: str) -> go.Figure:
    """Bar chart of new pipeline ARR per period."""
    if COL_ARR not in df.columns or time_col not in df.columns:
        return _empty_figure("No data for Pipeline Production")

    grouped = (
        df.groupby(time_col, dropna=False)[COL_ARR]
        .sum()
        .reset_index()
        .sort_values(time_col)
    )

    if grouped.empty:
        return _empty_figure("No deals in filtered data")

    fig = px.bar(
        grouped,
        x=time_col,
        y=COL_ARR,
        title="Pipeline Production Over Time",
        labels={COL_ARR: "New Pipeline ARR", time_col: "Period"},
        color_discrete_sequence=["#1E88E5"],
    )
    fig.update_layout(
        template="plotly_white",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
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
