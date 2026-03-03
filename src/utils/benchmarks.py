"""
Configurable benchmark model and evaluator.

Benchmarks are stored as a session-scoped table so users can adjust
thresholds without editing code.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

COLOR_MAP = {
    "red": "#E53935",
    "amber": "#FFA726",
    "green": "#43A047",
    "neutral": "#1E88E5",
}


DEFAULT_BENCHMARK_ROWS: list[dict] = [
    {
        "metric": "count_wr",
        "segment_by": "none",
        "segment_label": "All",
        "segment_min": None,
        "segment_max": None,
        "red_min": None,
        "red_max": 0.20,
        "amber_min": 0.20,
        "amber_max": 0.25,
        "green_min": 0.25,
        "green_max": None,
    },
    {
        "metric": "rev_wr",
        "segment_by": "none",
        "segment_label": "All",
        "segment_min": None,
        "segment_max": None,
        "red_min": None,
        "red_max": 0.20,
        "amber_min": 0.20,
        "amber_max": 0.25,
        "green_min": 0.25,
        "green_max": None,
    },
    {
        "metric": "pipeline_coverage",
        "segment_by": "none",
        "segment_label": "All",
        "segment_min": None,
        "segment_max": None,
        "red_min": None,
        "red_max": 2.0,
        "amber_min": 2.0,
        "amber_max": 3.0,
        "green_min": 3.0,
        "green_max": None,
    },
    {
        "metric": "avg_sales_cycle",
        "segment_by": "avg_deal_size",
        "segment_label": "ARR < 10K",
        "segment_min": 0.0,
        "segment_max": 10_000.0,
        "red_min": 30.0,
        "red_max": None,
        "amber_min": 14.0,
        "amber_max": 30.0,
        "green_min": None,
        "green_max": 14.0,
    },
    {
        "metric": "avg_sales_cycle",
        "segment_by": "avg_deal_size",
        "segment_label": "10K <= ARR <= 50K",
        "segment_min": 10_000.0,
        "segment_max": 50_000.0,
        "red_min": 60.0,
        "red_max": None,
        "amber_min": 45.0,
        "amber_max": 60.0,
        "green_min": None,
        "green_max": 45.0,
    },
    {
        "metric": "avg_sales_cycle",
        "segment_by": "avg_deal_size",
        "segment_label": "ARR > 50K",
        "segment_min": 50_000.0,
        "segment_max": None,
        "red_min": 120.0,
        "red_max": None,
        "amber_min": 90.0,
        "amber_max": 120.0,
        "green_min": None,
        "green_max": 90.0,
    },
    {
        "metric": "nrr",
        "segment_by": "current_arr",
        "segment_label": "ARR <= 1M",
        "segment_min": 0.0,
        "segment_max": 1_000_000.0,
        "red_min": None,
        "red_max": 1.00,
        "amber_min": 1.00,
        "amber_max": 1.10,
        "green_min": 1.10,
        "green_max": None,
    },
    {
        "metric": "nrr",
        "segment_by": "current_arr",
        "segment_label": "1M < ARR <= 5M",
        "segment_min": 1_000_000.0,
        "segment_max": 5_000_000.0,
        "red_min": None,
        "red_max": 1.00,
        "amber_min": 1.00,
        "amber_max": 1.10,
        "green_min": 1.10,
        "green_max": None,
    },
    {
        "metric": "nrr",
        "segment_by": "current_arr",
        "segment_label": "5M < ARR <= 15M",
        "segment_min": 5_000_000.0,
        "segment_max": 15_000_000.0,
        "red_min": None,
        "red_max": 1.05,
        "amber_min": 1.05,
        "amber_max": 1.20,
        "green_min": 1.20,
        "green_max": None,
    },
    {
        "metric": "arr_churn",
        "segment_by": "current_arr",
        "segment_label": "ARR <= 1M",
        "segment_min": 0.0,
        "segment_max": 1_000_000.0,
        "red_min": 0.20,
        "red_max": None,
        "amber_min": 0.10,
        "amber_max": 0.20,
        "green_min": None,
        "green_max": 0.10,
    },
    {
        "metric": "arr_churn",
        "segment_by": "current_arr",
        "segment_label": "1M < ARR <= 10M",
        "segment_min": 1_000_000.0,
        "segment_max": 10_000_000.0,
        "red_min": 0.12,
        "red_max": None,
        "amber_min": 0.08,
        "amber_max": 0.12,
        "green_min": None,
        "green_max": 0.08,
    },
    {
        "metric": "arr_churn",
        "segment_by": "current_arr",
        "segment_label": "ARR > 10M",
        "segment_min": 10_000_000.0,
        "segment_max": None,
        "red_min": 0.10,
        "red_max": None,
        "amber_min": 0.06,
        "amber_max": 0.10,
        "green_min": None,
        "green_max": 0.06,
    },
    {
        "metric": "logo_churn",
        "segment_by": "none",
        "segment_label": "All",
        "segment_min": None,
        "segment_max": None,
        "red_min": 0.15,
        "red_max": None,
        "amber_min": 0.05,
        "amber_max": 0.15,
        "green_min": None,
        "green_max": 0.05,
    },
]

_NUMERIC_COLS = [
    "segment_min",
    "segment_max",
    "red_min",
    "red_max",
    "amber_min",
    "amber_max",
    "green_min",
    "green_max",
]

_BENCHMARK_FILE = (
    Path(__file__).resolve().parents[2] / "config" / "benchmark_thresholds.json"
)


def _clean_number(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _in_range(value: float, min_val: float | None, max_val: float | None) -> bool:
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True


def _match_segment(row: pd.Series, context: dict[str, float | None]) -> bool:
    segment_by = str(row.get("segment_by", "none") or "none")
    if segment_by == "none":
        return True

    segment_value = context.get(segment_by)
    if segment_value is None or pd.isna(segment_value):
        return False

    segment_min = _clean_number(row.get("segment_min"))
    segment_max = _clean_number(row.get("segment_max"))

    if segment_min is not None and segment_value < segment_min:
        return False
    if segment_max is not None and segment_value > segment_max:
        return False
    return True


def _get_benchmark_df() -> pd.DataFrame:
    if "benchmark_df" not in st.session_state:
        loaded = _load_benchmark_file()
        if loaded is None:
            st.session_state["benchmark_df"] = pd.DataFrame(deepcopy(DEFAULT_BENCHMARK_ROWS))
        else:
            st.session_state["benchmark_df"] = loaded
    return st.session_state["benchmark_df"]


def _normalize_benchmark_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in _NUMERIC_COLS:
        if col in out.columns:
            out[col] = out[col].apply(_clean_number)
    return out


def _load_benchmark_file() -> pd.DataFrame | None:
    if not _BENCHMARK_FILE.exists():
        return None

    try:
        raw = json.loads(_BENCHMARK_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return None
        return _normalize_benchmark_df(pd.DataFrame(raw))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _load_benchmark_bytes(raw_bytes: bytes) -> pd.DataFrame | None:
    try:
        raw = json.loads(raw_bytes.decode("utf-8"))
        if not isinstance(raw, list):
            return None
        return _normalize_benchmark_df(pd.DataFrame(raw))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _save_benchmark_file(df: pd.DataFrame) -> tuple[bool, str]:
    try:
        _BENCHMARK_FILE.parent.mkdir(parents=True, exist_ok=True)
        normalized = _normalize_benchmark_df(df)
        payload = [
            {k: (None if pd.isna(v) else v) for k, v in row.items()}
            for row in normalized.to_dict(orient="records")
        ]
        _BENCHMARK_FILE.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        return True, f"Saved to {_BENCHMARK_FILE}"
    except OSError as exc:
        return False, f"Could not save benchmark file: {exc}"


def render_benchmark_editor() -> None:
    """Render editable benchmark table inside sidebar."""
    with st.sidebar.expander("🎯 Benchmark Thresholds", expanded=False):
        st.caption(
            "Edit thresholds for red/amber/green classification. "
            "Changes apply immediately for this session."
        )
        st.caption(
            "Note: ARR Churn amber/green defaults are conservative placeholders and can be adjusted."
        )

        benchmark_df = _get_benchmark_df()
        edited = st.data_editor(
            benchmark_df,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            key="benchmark_editor",
        )

        edited = _normalize_benchmark_df(edited)

        st.session_state["benchmark_df"] = edited

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Reset defaults", key="reset_benchmarks"):
                st.session_state["benchmark_df"] = pd.DataFrame(
                    deepcopy(DEFAULT_BENCHMARK_ROWS)
                )
                st.rerun()
        with c2:
            if st.button("Save", key="save_benchmarks"):
                ok, msg = _save_benchmark_file(st.session_state["benchmark_df"])
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        with c3:
            if st.button("Reload", key="reload_benchmarks"):
                loaded = _load_benchmark_file()
                if loaded is not None:
                    st.session_state["benchmark_df"] = loaded
                    st.rerun()
                st.warning("No saved benchmark file found.")

        st.markdown("---")
        st.caption("Preset sharing")

        export_payload = [
            {k: (None if pd.isna(v) else v) for k, v in row.items()}
            for row in st.session_state["benchmark_df"].to_dict(orient="records")
        ]
        export_name = f"benchmark_thresholds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        st.download_button(
            label="Export preset",
            data=json.dumps(export_payload, indent=2),
            file_name=export_name,
            mime="application/json",
            key="export_benchmark_preset",
            use_container_width=True,
        )

        upload_file = st.file_uploader(
            "Import preset",
            type=["json"],
            key="import_benchmark_preset",
            help="Upload a benchmark preset JSON exported from this app.",
        )
        if upload_file is not None:
            imported = _load_benchmark_bytes(upload_file.getvalue())
            if imported is None:
                st.error("Invalid benchmark preset file.")
            else:
                st.session_state["benchmark_df"] = imported
                st.success("Preset imported. Click Save to persist it on disk.")

        st.caption("Use blank cells for open-ended ranges.")
        st.caption(f"Persistence path: {_BENCHMARK_FILE}")


def evaluate_benchmark(
    metric: str,
    value: float | None,
    context: dict[str, float | None] | None = None,
) -> tuple[str, str]:
    """Return (color_hex, status_label) based on configurable thresholds."""
    if value is None or pd.isna(value):
        return COLOR_MAP["neutral"], "N/A"

    context = context or {}
    df = _get_benchmark_df()
    metric_rows = df[df["metric"] == metric]

    if metric_rows.empty:
        return COLOR_MAP["neutral"], "N/A"

    matched = metric_rows[metric_rows.apply(lambda row: _match_segment(row, context), axis=1)]
    if matched.empty:
        matched = metric_rows[metric_rows["segment_by"].astype(str) == "none"]

    if matched.empty:
        return COLOR_MAP["neutral"], "N/A"

    row = matched.iloc[0]

    if _in_range(value, _clean_number(row.get("green_min")), _clean_number(row.get("green_max"))):
        return COLOR_MAP["green"], "Green"
    if _in_range(value, _clean_number(row.get("amber_min")), _clean_number(row.get("amber_max"))):
        return COLOR_MAP["amber"], "Amber"
    if _in_range(value, _clean_number(row.get("red_min")), _clean_number(row.get("red_max"))):
        return COLOR_MAP["red"], "Red"

    return COLOR_MAP["neutral"], "N/A"
