"""
Conversion Funnel — stage progression analysis.
Shows deal count at each Deal Stage, ordered by pipeline progression.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from utils.constants import COL_DEAL_STAGE


# ---------------------------------------------------------------------------
# Funnel chart
# ---------------------------------------------------------------------------
def stage_conversion_funnel(df: pd.DataFrame) -> go.Figure:
    """Funnel chart showing deal count at each Deal Stage."""
    if COL_DEAL_STAGE not in df.columns:
        return _empty_figure("No Deal Stage data for funnel")

    stage_counts = (
        df[COL_DEAL_STAGE]
        .value_counts()
        .reset_index()
    )
    stage_counts.columns = ["Stage", "Count"]

    stage_order = [
        "prospecting",
        "qualification",
        "discovery",
        "proposal",
        "negotiation",
        "contract",
        "closed won",
        "closed lost",
    ]

    def _rank(stage: str) -> int:
        s = str(stage).strip().lower()
        for i, token in enumerate(stage_order):
            if token in s:
                return i
        return len(stage_order) + 1

    stage_counts["_rank"] = stage_counts["Stage"].map(_rank)
    stage_counts = stage_counts.sort_values(["_rank", "Count"], ascending=[True, False]).drop(columns=["_rank"])

    if stage_counts.empty:
        return _empty_figure("No deals in filtered data")

    fig = go.Figure(
        go.Funnel(
            y=stage_counts["Stage"],
            x=stage_counts["Count"],
            textinfo="value+percent initial",
            marker=dict(
                color=[
                    "#1E3A5F", "#2F5D8A", "#3F7AAE", "#5B95C7",
                    "#5E6B73", "#7A868D", "#2E7D32", "#C62828",
                ][: len(stage_counts)],
            ),
        )
    )

    fig.update_layout(
        title="Deal Conversion Funnel",
        template="plotly_white",
        height=max(350, len(stage_counts) * 50 + 100),
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
