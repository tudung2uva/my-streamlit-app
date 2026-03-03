"""
Churn metrics — Logo Churn and ARR Churn.

Logo Churn:
  Churned Customers (non-null Churn Date) / Starting Customers (ARR per 1/1 > 0)

ARR Churn:
  SUM(Churn ARR) / SUM(Starting ARR)

Both metrics de-duplicate by Customer Name before aggregation to avoid
double-counting across multiple deal rows for the same customer.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.constants import (
    COL_ARR_START,
    COL_CHURN_ARR,
    COL_CHURN_DATE,
    COL_CUSTOMER_NAME,
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers — fiscal period derivation for Churn Date
# ═══════════════════════════════════════════════════════════════════════════

def _add_churn_fiscal_cols(df: pd.DataFrame, fy_start_month: int = 1) -> pd.DataFrame:
    """Add _Churn Fiscal Year / Quarter / Month / Week derived from COL_CHURN_DATE."""
    out = df.copy()
    if COL_CHURN_DATE not in out.columns:
        return out

    dt = out[COL_CHURN_DATE]

    if fy_start_month == 1:
        out["_Churn Fiscal Year"] = (
            dt.dt.year.astype("Int64").astype(str).replace("<NA>", None)
        )
        out["_Churn Fiscal Quarter"] = dt.dt.to_period("Q").astype(str)
    else:
        offset = fy_start_month - 1
        shifted = dt - pd.DateOffset(months=offset)
        out["_Churn Fiscal Year"] = (
            "FY" + shifted.dt.year.astype("Int64").astype(str).replace("<NA>", None)
        )
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
    """Map a deal-creation time_col to its churn-date equivalent."""
    mapping = {
        "_Fiscal Year": "_Churn Fiscal Year",
        "_Fiscal Quarter": "_Churn Fiscal Quarter",
        "_Fiscal Month": "_Churn Fiscal Month",
        "_Fiscal Week": "_Churn Fiscal Week",
    }
    return mapping.get(time_col, "_Churn Fiscal Year")


def _dedup_customers(df: pd.DataFrame) -> pd.DataFrame:
    """If Customer Name exists, keep one row per customer (max ARR per 1/1)."""
    if COL_CUSTOMER_NAME in df.columns:
        sort_col = COL_ARR_START if COL_ARR_START in df.columns else None
        if sort_col:
            return df.sort_values(sort_col, ascending=False).drop_duplicates(
                subset=[COL_CUSTOMER_NAME], keep="first"
            )
        return df.drop_duplicates(subset=[COL_CUSTOMER_NAME], keep="first")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# LOGO CHURN
# ═══════════════════════════════════════════════════════════════════════════

def logo_churn_kpi(df: pd.DataFrame) -> tuple[int, int, float]:
    """Return (churned_logos, starting_logos, churn_pct).

    Churned = distinct customers with non-null Churn Date.
    Starting = distinct customers with ARR per 1/1 > 0.
    """
    deduped = _dedup_customers(df)

    starting = 0
    if COL_ARR_START in deduped.columns:
        starting = int((deduped[COL_ARR_START].fillna(0) > 0).sum())

    churned = 0
    if COL_CHURN_DATE in deduped.columns:
        churned = int(deduped[COL_CHURN_DATE].notna().sum())

    pct = churned / starting if starting > 0 else 0.0
    return churned, starting, pct


def logo_churn_over_time_chart(
    df: pd.DataFrame, time_col: str, fy_start_month: int = 1
) -> go.Figure:
    """Bar chart of churned logos per period (based on Churn Date)."""
    if COL_CHURN_DATE not in df.columns:
        return _empty_figure("No Churn Date data for Logo Churn")

    enriched = _add_churn_fiscal_cols(df, fy_start_month)
    churn_tc = _churn_time_col(time_col)

    if churn_tc not in enriched.columns:
        return _empty_figure("Cannot derive churn fiscal period")

    churned = enriched[enriched[COL_CHURN_DATE].notna()].copy()
    if COL_CUSTOMER_NAME in churned.columns:
        churned = churned.drop_duplicates(subset=[COL_CUSTOMER_NAME, churn_tc], keep="first")

    if churned.empty:
        return _empty_figure("No churned customers in filtered data")

    grouped = (
        churned.groupby(churn_tc, dropna=False)
        .size()
        .reset_index(name="Churned Logos")
        .sort_values(churn_tc)
    )

    fig = px.bar(
        grouped,
        x=churn_tc,
        y="Churned Logos",
        title="Logo Churn Over Time",
        labels={"Churned Logos": "Churned Customers", churn_tc: "Period"},
        color_discrete_sequence=["#C62828"],
        text="Churned Logos",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(template="plotly_white")
    return fig


def logo_churn_detail_table(
    df: pd.DataFrame, time_col: str, fy_start_month: int = 1
) -> pd.DataFrame | None:
    """Per-period Logo Churn breakdown."""
    if COL_CHURN_DATE not in df.columns or COL_ARR_START not in df.columns:
        return None

    enriched = _add_churn_fiscal_cols(df, fy_start_month)
    churn_tc = _churn_time_col(time_col)
    if churn_tc not in enriched.columns:
        return None

    deduped = _dedup_customers(enriched)

    # Starting logos per period — use the creation-date based time_col for starting
    # but churn is grouped by churn_tc
    starting_total = int((deduped[COL_ARR_START].fillna(0) > 0).sum())

    churned = enriched[enriched[COL_CHURN_DATE].notna()].copy()
    if COL_CUSTOMER_NAME in churned.columns:
        churned = churned.drop_duplicates(subset=[COL_CUSTOMER_NAME, churn_tc], keep="first")

    if churned.empty:
        return None

    grouped = (
        churned.groupby(churn_tc, dropna=False)
        .size()
        .reset_index(name="Churned Logos")
        .sort_values(churn_tc)
    )
    grouped["Starting Logos"] = starting_total
    grouped["Logo Churn %"] = grouped["Churned Logos"] / starting_total * 100
    grouped = grouped.rename(columns={churn_tc: "Period"})
    return grouped[["Period", "Starting Logos", "Churned Logos", "Logo Churn %"]]


# ═══════════════════════════════════════════════════════════════════════════
# ARR CHURN
# ═══════════════════════════════════════════════════════════════════════════

def arr_churn_kpi(df: pd.DataFrame) -> tuple[float, float, float]:
    """Return (churn_arr, starting_arr, churn_pct).

    Churn ARR = SUM of COL_CHURN_ARR (deduped by customer).
    Starting ARR = SUM of COL_ARR_START (deduped by customer).
    """
    deduped = _dedup_customers(df)

    starting_arr = 0.0
    if COL_ARR_START in deduped.columns:
        starting_arr = float(deduped[COL_ARR_START].fillna(0).sum())

    churn_arr = 0.0
    if COL_CHURN_ARR in deduped.columns:
        churn_arr = float(deduped[COL_CHURN_ARR].fillna(0).sum())

    pct = churn_arr / starting_arr if starting_arr > 0 else 0.0
    return churn_arr, starting_arr, pct


def arr_churn_over_time_chart(
    df: pd.DataFrame, time_col: str, fy_start_month: int = 1
) -> go.Figure:
    """Bar chart of churned ARR per period (based on Churn Date)."""
    if COL_CHURN_ARR not in df.columns or COL_CHURN_DATE not in df.columns:
        return _empty_figure("No Churn ARR / Churn Date data")

    enriched = _add_churn_fiscal_cols(df, fy_start_month)
    churn_tc = _churn_time_col(time_col)
    if churn_tc not in enriched.columns:
        return _empty_figure("Cannot derive churn fiscal period")

    churned = enriched[enriched[COL_CHURN_DATE].notna()].copy()
    if COL_CUSTOMER_NAME in churned.columns:
        churned = churned.drop_duplicates(subset=[COL_CUSTOMER_NAME, churn_tc], keep="first")

    if churned.empty:
        return _empty_figure("No churn records in filtered data")

    grouped = (
        churned.groupby(churn_tc, dropna=False)[COL_CHURN_ARR]
        .sum()
        .reset_index(name="Churn ARR")
        .sort_values(churn_tc)
    )

    fig = px.bar(
        grouped,
        x=churn_tc,
        y="Churn ARR",
        title="ARR Churn Over Time",
        labels={"Churn ARR": "Churned ARR", churn_tc: "Period"},
        color_discrete_sequence=["#C62828"],
        text="Churn ARR",
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
    )
    return fig


def arr_churn_detail_table(
    df: pd.DataFrame, time_col: str, fy_start_month: int = 1
) -> pd.DataFrame | None:
    """Per-period ARR Churn breakdown."""
    if COL_CHURN_ARR not in df.columns or COL_ARR_START not in df.columns:
        return None

    enriched = _add_churn_fiscal_cols(df, fy_start_month)
    churn_tc = _churn_time_col(time_col)
    if churn_tc not in enriched.columns:
        return None

    deduped = _dedup_customers(enriched)
    starting_arr = float(deduped[COL_ARR_START].fillna(0).sum())

    churned = enriched[enriched[COL_CHURN_DATE].notna()].copy()
    if COL_CUSTOMER_NAME in churned.columns:
        churned = churned.drop_duplicates(subset=[COL_CUSTOMER_NAME, churn_tc], keep="first")

    if churned.empty:
        return None

    grouped = (
        churned.groupby(churn_tc, dropna=False)[COL_CHURN_ARR]
        .sum()
        .reset_index(name="Churn ARR")
        .sort_values(churn_tc)
    )
    grouped["Starting ARR"] = starting_arr
    grouped["ARR Churn %"] = grouped["Churn ARR"] / starting_arr * 100
    grouped = grouped.rename(columns={churn_tc: "Period"})
    return grouped[["Period", "Starting ARR", "Churn ARR", "ARR Churn %"]]


# ═══════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════

def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(template="plotly_white", height=300)
    return fig
