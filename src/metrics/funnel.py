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
    stage_counts = stage_counts.sort_values("Count", ascending=False)

    if stage_counts.empty:
        return _empty_figure("No deals in filtered data")

    fig = go.Figure(
        go.Funnel(
            y=stage_counts["Stage"],
            x=stage_counts["Count"],
            textinfo="value+percent initial",
            marker=dict(
                color=[
                    "#1E88E5", "#42A5F5", "#64B5F6", "#90CAF9",
                    "#43A047", "#66BB6A", "#81C784", "#A5D6A7",
                    "#FFA726", "#FFB74D", "#FFCC80", "#FFE0B2",
                    "#E53935", "#EF5350", "#E57373", "#EF9A9A",
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
