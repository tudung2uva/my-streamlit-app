"""
Net Revenue Retention (NRR) metric.
Formula:
  NRR = (Starting ARR + Expansion ARR − Churn ARR) / Starting ARR

  Starting ARR = SUM(ARR per 1/1) — de-duplicated by Customer Name
  Expansion ARR = SUM(ARR Amount) where Deal Type ∈ {Upsell, Cross-sell} AND Closed Won
  Churn ARR = SUM(Churn ARR column) — de-duplicated by Customer Name
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from utils.constants import (
    COL_ARR,
    COL_ARR_START,
    COL_CHURN_ARR,
    COL_CHURN_DATE,
    COL_CUSTOMER_NAME,
    COL_DEAL_TYPE,
    COL_IS_CLOSED_WON,
)

_EXPANSION_TYPES = {"upsell", "cross-sell", "cross sell", "crosssell"}


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _dedup_customers(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Keep one row per customer, preferring the row with the highest value_col."""
    if COL_CUSTOMER_NAME in df.columns and value_col in df.columns:
        return (
            df.sort_values(value_col, ascending=False)
            .drop_duplicates(subset=[COL_CUSTOMER_NAME], keep="first")
        )
    return df


def _get_starting_arr(df: pd.DataFrame) -> float:
    """SUM(ARR per 1/1) de-duplicated by customer."""
    if COL_ARR_START not in df.columns:
        return 0.0
    deduped = _dedup_customers(df, COL_ARR_START)
    return float(deduped[COL_ARR_START].fillna(0).sum())


def _get_expansion_arr(df: pd.DataFrame) -> float:
    """SUM(ARR) for won upsell / cross-sell deals."""
    if COL_ARR not in df.columns or COL_DEAL_TYPE not in df.columns:
        return 0.0
    mask = (
        df[COL_DEAL_TYPE].astype(str).str.strip().str.lower().isin(_EXPANSION_TYPES)
        & df[COL_IS_CLOSED_WON]
    )
    return float(df.loc[mask, COL_ARR].sum())


def _get_churn_arr(df: pd.DataFrame) -> float:
    """SUM(Churn ARR) de-duplicated by customer."""
    if COL_CHURN_ARR not in df.columns:
        return 0.0
    deduped = _dedup_customers(df, COL_CHURN_ARR)
    return float(deduped[COL_CHURN_ARR].fillna(0).sum())


def _add_churn_fiscal_cols(df: pd.DataFrame, fy_start_month: int = 1) -> pd.DataFrame:
    """Derive churn-date fiscal period columns (mirrors helpers.add_derived_columns)."""
    out = df.copy()
    if COL_CHURN_DATE not in out.columns:
        return out

    dt = out[COL_CHURN_DATE]
    if fy_start_month == 1:
        out["_Churn Fiscal Year"] = dt.dt.year.astype("Int64").astype(str).replace("<NA>", None)
        out["_Churn Fiscal Quarter"] = dt.dt.to_period("Q").astype(str)
    else:
        offset = fy_start_month - 1
        shifted = dt - pd.DateOffset(months=offset)
        out["_Churn Fiscal Year"] = "FY" + shifted.dt.year.astype("Int64").astype(str).replace("<NA>", None)
        fiscal_month_num = ((dt.dt.month - fy_start_month) % 12) + 1
        fiscal_qtr = ((fiscal_month_num - 1) // 3) + 1
        out["_Churn Fiscal Quarter"] = out["_Churn Fiscal Year"] + "-Q" + fiscal_qtr.astype(str)

    out["_Churn Fiscal Month"] = dt.dt.to_period("M").astype(str)
    out["_Churn Fiscal Week"] = (
        dt.dt.isocalendar().year.astype(str)
        + "-W"
        + dt.dt.isocalendar().week.astype(str).str.zfill(2)
    )
    return out


def _churn_time_col(time_col: str) -> str:
    mapping = {
        "_Fiscal Year": "_Churn Fiscal Year",
        "_Fiscal Quarter": "_Churn Fiscal Quarter",
        "_Fiscal Month": "_Churn Fiscal Month",
        "_Fiscal Week": "_Churn Fiscal Week",
    }
    return mapping.get(time_col, "_Churn Fiscal Year")


# ═══════════════════════════════════════════════════════════════════════════
# KPI
# ═══════════════════════════════════════════════════════════════════════════

def nrr_kpi(df: pd.DataFrame) -> float:
    """Net Revenue Retention as a ratio (e.g. 1.12 = 112%)."""
    starting = _get_starting_arr(df)
    if starting <= 0:
        return 0.0
    expansion = _get_expansion_arr(df)
    churn = _get_churn_arr(df)
    return (starting + expansion - churn) / starting


# ═══════════════════════════════════════════════════════════════════════════
# Over-time chart
# ═══════════════════════════════════════════════════════════════════════════

def nrr_over_time_chart(
    df: pd.DataFrame, time_col: str, fy_start_month: int = 1
) -> go.Figure:
    """Bar chart of NRR components per period with a line for NRR %."""
    table = nrr_detail_table(df, time_col, fy_start_month)
    if table is None or table.empty:
        return _empty_figure("No data for NRR over time")

    fig = go.Figure()

    # Stacked bars for components
    fig.add_trace(go.Bar(
        x=table["Period"], y=table["Starting ARR"],
        name="Starting ARR", marker_color="#1565C0",
    ))
    fig.add_trace(go.Bar(
        x=table["Period"], y=table["Expansion ARR"],
        name="Expansion ARR", marker_color="#2E7D32",
    ))
    fig.add_trace(go.Bar(
        x=table["Period"], y=-table["Churn ARR"],
        name="Churn ARR", marker_color="#C62828",
    ))

    # NRR % line on secondary axis
    fig.add_trace(go.Scatter(
        x=table["Period"], y=table["NRR %"],
        name="NRR %", mode="lines+markers",
        line=dict(color="#FF6F00", width=3),
        yaxis="y2",
    ))

    fig.update_layout(
        title="Net Revenue Retention Over Time",
        barmode="relative",
        template="plotly_white",
        yaxis=dict(title="ARR ($)", tickprefix="$", tickformat=","),
        yaxis2=dict(
            title="NRR %", overlaying="y", side="right",
            ticksuffix="%", showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Detail table
# ═══════════════════════════════════════════════════════════════════════════

def nrr_detail_table(
    df: pd.DataFrame, time_col: str, fy_start_month: int = 1
) -> pd.DataFrame | None:
    """Per-period NRR breakdown.

    Expansion is grouped by the deal's fiscal period (creation date);
    Churn is grouped by churn-date fiscal period.
    Starting ARR is the same baseline per period (total deduped starting).
    """
    if COL_ARR_START not in df.columns:
        return None

    starting_arr = _get_starting_arr(df)
    if starting_arr <= 0:
        return None

    # Expansion per (creation-date) period
    has_expansion = COL_DEAL_TYPE in df.columns and COL_ARR in df.columns
    expansion_by_period: dict = {}
    if has_expansion and time_col in df.columns:
        mask = (
            df[COL_DEAL_TYPE].astype(str).str.strip().str.lower().isin(_EXPANSION_TYPES)
            & df[COL_IS_CLOSED_WON]
        )
        exp_df = df.loc[mask]
        if not exp_df.empty:
            expansion_by_period = (
                exp_df.groupby(time_col, dropna=False)[COL_ARR]
                .sum()
                .to_dict()
            )

    # Churn per (churn-date) period
    has_churn = COL_CHURN_ARR in df.columns and COL_CHURN_DATE in df.columns
    churn_by_period: dict = {}
    if has_churn:
        enriched = _add_churn_fiscal_cols(df, fy_start_month)
        churn_tc = _churn_time_col(time_col)
        if churn_tc in enriched.columns:
            churned = enriched[enriched[COL_CHURN_DATE].notna()].copy()
            if COL_CUSTOMER_NAME in churned.columns:
                churned = churned.drop_duplicates(
                    subset=[COL_CUSTOMER_NAME, churn_tc], keep="first"
                )
            if not churned.empty:
                churn_by_period = (
                    churned.groupby(churn_tc, dropna=False)[COL_CHURN_ARR]
                    .sum()
                    .to_dict()
                )

    # Merge all periods
    all_periods = sorted(set(list(expansion_by_period.keys()) + list(churn_by_period.keys())))
    if not all_periods:
        return None

    records = []
    for period in all_periods:
        exp = expansion_by_period.get(period, 0.0)
        churn = churn_by_period.get(period, 0.0)
        ending = starting_arr + exp - churn
        nrr_pct = (starting_arr + exp - churn) / starting_arr * 100 if starting_arr > 0 else 0

        records.append({
            "Period": str(period),
            "Starting ARR": starting_arr,
            "Expansion ARR": exp,
            "Churn ARR": churn,
            "Ending ARR": ending,
            "NRR %": round(nrr_pct, 1),
        })

    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════

def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
