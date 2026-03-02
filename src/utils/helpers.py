"""
Data loading, parsing, and cleaning utilities.
Handles delimiter detection, column alias mapping, European number formats,
date parsing, and derived column creation.
"""

from __future__ import annotations

import io
import re
from typing import Optional

import pandas as pd
import streamlit as st

from utils.constants import (
    COLUMN_ALIASES,
    COL_ARR,
    COL_ARR_START,
    COL_CHURN_ARR,
    COL_CHURN_DATE,
    COL_CLOSE_DATE,
    COL_CREATION_DATE,
    COL_DAYS_TO_CLOSE,
    COL_DEAL_STAGE,
    COL_FISCAL_MONTH,
    COL_FISCAL_QUARTER,
    COL_FISCAL_WEEK,
    COL_FISCAL_YEAR,
    COL_IS_CLOSED_LOST,
    COL_IS_CLOSED_WON,
    COL_IS_OPEN,
    STAGE_CLOSED_LOST,
    STAGE_CLOSED_WON,
)


# ---------------------------------------------------------------------------
# 1. Delimiter detection
# ---------------------------------------------------------------------------
def detect_delimiter(raw_bytes: bytes) -> str:
    """Sniff first line to decide between `;` and `,`."""
    first_line = raw_bytes.split(b"\n")[0].decode("utf-8", errors="replace")
    if first_line.count(";") > first_line.count(","):
        return ";"
    return ","


# ---------------------------------------------------------------------------
# 2. Column alias mapping
# ---------------------------------------------------------------------------
def _build_reverse_alias_map() -> dict[str, str]:
    """Return {alias_lower: canonical_name}."""
    rev: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            rev[alias.strip().lower()] = canonical
    return rev


_REVERSE_ALIASES = _build_reverse_alias_map()


def apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns that match known aliases to canonical names."""
    rename_map: dict[str, str] = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in _REVERSE_ALIASES:
            canonical = _REVERSE_ALIASES[key]
            # Only rename if the canonical name isn't already present
            if canonical not in df.columns and canonical not in rename_map.values():
                rename_map[col] = canonical
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


# ---------------------------------------------------------------------------
# 3. Numeric parsing (handles European format like $12.500,00)
# ---------------------------------------------------------------------------
def parse_currency(series: pd.Series) -> pd.Series:
    """Convert a currency series to float, handling European formatting."""
    if series.dtype in ("float64", "int64", "float32", "int32"):
        return series.astype(float)

    s = series.astype(str)

    # Detect European format: presence of patterns like 12.500,00
    sample = s.dropna().head(50).str.cat(sep=" ")
    is_european = bool(re.search(r"\d{1,3}\.\d{3}", sample) and "," in sample)

    if is_european:
        # Strip currency symbols and whitespace
        s = s.str.replace(r"[€$£¥\s]", "", regex=True)
        # Remove thousands separator (.)
        s = s.str.replace(".", "", regex=False)
        # Decimal separator (, → .)
        s = s.str.replace(",", ".", regex=False)
    else:
        # Standard format: strip currency symbols, remove commas
        s = s.str.replace(r"[€$£¥\s]", "", regex=True)
        s = s.str.replace(",", "", regex=False)

    return pd.to_numeric(s, errors="coerce")


# ---------------------------------------------------------------------------
# 4. Date parsing
# ---------------------------------------------------------------------------
def parse_dates(series: pd.Series) -> pd.Series:
    """Parse dates trying DD/MM/YYYY first, then falling back."""
    # Strip leading ? characters (seen in Book1.csv year columns)
    cleaned = series.astype(str).str.lstrip("?").str.strip()
    cleaned = cleaned.replace({"": pd.NaT, "nan": pd.NaT, "NaT": pd.NaT, "None": pd.NaT})

    try:
        return pd.to_datetime(cleaned, dayfirst=True, format="mixed")
    except Exception:
        try:
            return pd.to_datetime(cleaned, dayfirst=True, infer_datetime_format=True)
        except Exception:
            return pd.to_datetime(cleaned, errors="coerce")


# ---------------------------------------------------------------------------
# 5. Currency formatting (display only)
# ---------------------------------------------------------------------------
def format_currency(value: float, symbol: str = "€", short: bool = True) -> str:
    """Format a numeric value for display with currency symbol.

    Ported from JS ``fmtC()`` / ``fmtCS()``:
      ≥ 1 M  → €1.23M
      ≥ 1 K  → €1.2K
      else   → €123
    When *short* is False, always uses full format with commas: €1,234,567.
    """
    if value is None or pd.isna(value):
        return f"{symbol}0"
    v = float(value)
    if not short:
        return f"{symbol}{v:,.0f}"
    abs_v = abs(v)
    if abs_v >= 1_000_000:
        return f"{symbol}{v / 1_000_000:,.2f}M"
    if abs_v >= 1_000:
        return f"{symbol}{v / 1_000:,.1f}K"
    return f"{symbol}{v:,.0f}"


# ---------------------------------------------------------------------------
# 6. Derive helper columns
# ---------------------------------------------------------------------------
def add_derived_columns(
    df: pd.DataFrame, fy_start_month: int = 1
) -> pd.DataFrame:
    """Add boolean flags, time dimensions, and sales cycle days.

    Parameters
    ----------
    fy_start_month : int
        First month of the fiscal year (1 = Jan, 4 = Apr, 7 = Jul, …).
        Fiscal year is labelled by the *calendar year the FY ends in*
        when fy_start_month > 1.
    """
    # Normalise Deal Stage for comparison
    stage = df[COL_DEAL_STAGE].astype(str).str.strip()

    df[COL_IS_CLOSED_WON] = stage.str.lower() == STAGE_CLOSED_WON.lower()
    df[COL_IS_CLOSED_LOST] = stage.str.lower() == STAGE_CLOSED_LOST.lower()
    df[COL_IS_OPEN] = ~(df[COL_IS_CLOSED_WON] | df[COL_IS_CLOSED_LOST])

    # Time dimensions from Deal Creation Date
    if COL_CREATION_DATE in df.columns:
        dt = df[COL_CREATION_DATE]

        if fy_start_month == 1:
            # Standard calendar year — simple logic
            df[COL_FISCAL_YEAR] = (
                dt.dt.year.astype("Int64").astype(str).replace("<NA>", None)
            )
            df[COL_FISCAL_QUARTER] = dt.dt.to_period("Q").astype(str)
        else:
            # Offset fiscal year
            offset = fy_start_month - 1  # months to shift back
            shifted = dt - pd.DateOffset(months=offset)
            df[COL_FISCAL_YEAR] = (
                "FY"
                + shifted.dt.year.astype("Int64").astype(str).replace("<NA>", None)
            )
            fiscal_month_num = ((dt.dt.month - fy_start_month) % 12) + 1
            fiscal_qtr = ((fiscal_month_num - 1) // 3) + 1
            df[COL_FISCAL_QUARTER] = df[COL_FISCAL_YEAR] + "-Q" + fiscal_qtr.astype(str)

        df[COL_FISCAL_MONTH] = dt.dt.to_period("M").astype(str)
        df[COL_FISCAL_WEEK] = (
            dt.dt.isocalendar().year.astype(str)
            + "-W"
            + dt.dt.isocalendar().week.astype(str).str.zfill(2)
        )

    # Sales cycle (days) for won deals
    if COL_CLOSE_DATE in df.columns and COL_CREATION_DATE in df.columns:
        df[COL_DAYS_TO_CLOSE] = (df[COL_CLOSE_DATE] - df[COL_CREATION_DATE]).dt.days

    return df


# ---------------------------------------------------------------------------
# 7. Main loader entry point
# ---------------------------------------------------------------------------
def load_and_parse(uploaded_file) -> pd.DataFrame:
    """
    Full pipeline: read uploaded file → alias mapping → type coercion →
    derived columns. Returns a clean DataFrame ready for analysis.
    """
    raw = uploaded_file.getvalue()
    name: str = uploaded_file.name

    # --- Read raw data ---
    if name.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    else:
        delimiter = detect_delimiter(raw)
        df = pd.read_csv(io.BytesIO(raw), sep=delimiter, encoding="utf-8-sig")

    # Strip whitespace from column names
    df.columns = [c.strip() for c in df.columns]

    # Drop fully-empty trailing columns (e.g. "Add your own formula")
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed|^Add your own", case=False, na=False)]

    # --- Alias mapping ---
    df = apply_column_aliases(df)

    # --- Numeric columns ---
    for col in [COL_ARR, COL_ARR_START, COL_CHURN_ARR]:
        if col in df.columns:
            df[col] = parse_currency(df[col])

    # --- Date columns ---
    for col in [COL_CREATION_DATE, COL_CLOSE_DATE, COL_CHURN_DATE]:
        if col in df.columns:
            df[col] = parse_dates(df[col])

    # --- Derived columns ---
    if COL_DEAL_STAGE in df.columns:
        df = add_derived_columns(df)

    return df
