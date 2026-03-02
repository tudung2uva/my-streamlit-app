"""
Concentration analysis.
From pars.md:
  Pivot tables showing ARR proportion by Region/Country, Deal Owner,
  Industry, Product/Product Tier, or Pipeline (for open deals).
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import (
    COL_ARR,
    COL_IS_OPEN,
    COL_PIPELINE,
    CONCENTRATION_DIMENSIONS,
)


def concentration_table(df: pd.DataFrame, group_col: str) -> pd.DataFrame | None:
    """
    Pivot: group by dimension, sum ARR, calculate % of total.
    For Pipeline dimension, filter to open deals only.
    Returns a summary DataFrame or None if data unavailable.
    """
    if COL_ARR not in df.columns or group_col not in df.columns:
        return None

    # Pipeline concentration uses open deals only
    if group_col == COL_PIPELINE and COL_IS_OPEN in df.columns:
        subset = df[df[COL_IS_OPEN]]
    else:
        subset = df

    if subset.empty:
        return None

    grouped = (
        subset.groupby(group_col, dropna=False)[COL_ARR]
        .agg(["sum", "count"])
        .reset_index()
    )
    grouped.columns = [group_col, "Total ARR", "Deal Count"]
    total_arr = grouped["Total ARR"].sum()
    grouped["% of Total"] = (grouped["Total ARR"] / total_arr * 100).round(1) if total_arr > 0 else 0
    grouped = grouped.sort_values("Total ARR", ascending=False)
    return grouped


def concentration_bar_chart(
    df: pd.DataFrame, group_col: str, label: str, top_n: int = 15
) -> go.Figure:
    """Horizontal bar chart of ARR share by dimension."""
    summary = concentration_table(df, group_col)
    if summary is None or summary.empty:
        return _empty_figure(f"No data for Concentration by {label}")

    # Limit to top N to keep chart readable
    plot_data = summary.head(top_n).sort_values("Total ARR", ascending=True)

    fig = px.bar(
        plot_data,
        y=group_col,
        x="Total ARR",
        orientation="h",
        title=f"ARR Concentration by {label}",
        labels={"Total ARR": "ARR ($)", group_col: label},
        text="% of Total",
        color_discrete_sequence=["#1E88E5"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        xaxis_tickprefix="$",
        xaxis_tickformat=",",
        showlegend=False,
        height=max(350, len(plot_data) * 35 + 100),
    )
    return fig


def get_available_dimensions(df: pd.DataFrame) -> list[dict]:
    """Return only concentration dimensions whose columns exist in the DataFrame."""
    available = []
    for dim in CONCENTRATION_DIMENSIONS:
        if dim["column"] in df.columns:
            available.append(dim)
    return available


def concentration_stats(df: pd.DataFrame, group_col: str) -> dict | None:
    """
    Compute top-N concentration statistics.
    Returns dict with keys: top_1_pct, top_3_pct, top_10_pct, label.
    Label: 'Diversified' / 'Moderate' / 'Concentrated'.
    Ported from render.js renderConcentrationPane().
    """
    tbl = concentration_table(df, group_col)
    if tbl is None or tbl.empty:
        return None

    pcts = tbl["% of Total"].values  # already sorted descending
    n = len(pcts)

    top_1_pct = float(pcts[0]) if n >= 1 else 0.0
    top_3_pct = float(pcts[:3].sum()) if n >= 3 else float(pcts.sum())
    top_10_pct = float(pcts[:10].sum()) if n >= 10 else float(pcts.sum())

    # Classify
    if top_1_pct >= 30 or top_3_pct >= 60:
        label = "Concentrated"
    elif top_1_pct >= 15 or top_3_pct >= 40:
        label = "Moderate"
    else:
        label = "Diversified"

    return {
        "top_1_pct": round(top_1_pct, 1),
        "top_3_pct": round(top_3_pct, 1),
        "top_10_pct": round(top_10_pct, 1),
        "label": label,
    }


def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
