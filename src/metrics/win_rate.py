"""
Win Rate metrics (count-based and revenue-based).
Formula from pars.md:
  Count-based:   Closed Won / (Closed Won + Closed Lost + Open)
  Revenue-based: Same ratio weighted by ARR Amount
  Cohort by Deal Creation Date, grouped by selected time increment.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import (
    COL_ARR,
    COL_IS_CLOSED_LOST,
    COL_IS_CLOSED_WON,
    COL_IS_OPEN,
)


def _compute_rates(df: pd.DataFrame, time_col: str) -> pd.DataFrame:
    """Aggregate win-rate stats per time bucket."""
    groups = df.groupby(time_col, dropna=False)

    records = []
    for name, grp in groups:
        won = grp[COL_IS_CLOSED_WON].sum()
        lost = grp[COL_IS_CLOSED_LOST].sum()
        opn = grp[COL_IS_OPEN].sum()
        total = won + lost + opn

        count_wr = won / total if total > 0 else 0

        arr_won = grp.loc[grp[COL_IS_CLOSED_WON], COL_ARR].sum() if COL_ARR in grp.columns else 0
        arr_total = grp[COL_ARR].sum() if COL_ARR in grp.columns else 0
        rev_wr = arr_won / arr_total if arr_total > 0 else 0

        records.append(
            {
                "Period": str(name),
                "Won": int(won),
                "Lost": int(lost),
                "Open": int(opn),
                "Total": int(total),
                "Count Win Rate": round(count_wr, 4),
                "Revenue Win Rate": round(rev_wr, 4),
                "ARR Won": arr_won,
                "ARR Total": arr_total,
            }
        )

    return pd.DataFrame(records)


# ---- KPI values (overall, unsliced by time) ----

def count_win_rate_kpi(df: pd.DataFrame) -> float:
    """Overall count-based win rate as a decimal (0-1)."""
    won = df[COL_IS_CLOSED_WON].sum()
    lost = df[COL_IS_CLOSED_LOST].sum()
    opn = df[COL_IS_OPEN].sum()
    total = won + lost + opn
    return won / total if total > 0 else 0


def revenue_win_rate_kpi(df: pd.DataFrame) -> float:
    """Overall revenue-based win rate as a decimal (0-1)."""
    if COL_ARR not in df.columns:
        return 0
    arr_won = df.loc[df[COL_IS_CLOSED_WON], COL_ARR].sum()
    arr_lost = df.loc[df[COL_IS_CLOSED_LOST], COL_ARR].sum()
    arr_open = df.loc[df[COL_IS_OPEN], COL_ARR].sum()
    arr_total = arr_won + arr_lost + arr_open
    return arr_won / arr_total if arr_total > 0 else 0


# ---- Charts ----

def win_rate_over_time_chart(df: pd.DataFrame, time_col: str) -> go.Figure:
    """Dual-axis line chart of count and revenue win rate over time."""
    rates = _compute_rates(df, time_col)
    if rates.empty:
        return _empty_figure("No data for Win Rate over time")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=rates["Period"],
            y=rates["Total"],
            name="Total Deals",
            marker_color="rgba(200,200,200,0.5)",
            yaxis="y2",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=rates["Period"],
            y=[r * 100 for r in rates["Count Win Rate"]],
            name="Count Win Rate %",
            mode="lines+markers",
            line=dict(color="#1E88E5", width=2.5),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=rates["Period"],
            y=[r * 100 for r in rates["Revenue Win Rate"]],
            name="Revenue Win Rate %",
            mode="lines+markers",
            line=dict(color="#43A047", width=2.5),
        )
    )

    max_deals = int(rates["Total"].max()) if not rates.empty else 10

    fig.update_layout(
        title="Win Rate Over Time",
        xaxis_title="Period",
        yaxis=dict(title="Win Rate (%)", range=[0, 105], side="left"),
        yaxis2=dict(
            title="Total Deals",
            overlaying="y",
            side="right",
            range=[0, max_deals * 2],
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_white",
    )
    return fig


def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
