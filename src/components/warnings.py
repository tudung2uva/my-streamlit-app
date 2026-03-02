"""
Column validation: compare uploaded DataFrame against the canonical schema.
Computes metric_flags for graceful degradation — never blocks the dashboard.
"""

import streamlit as st

from utils.constants import (
    METRIC_REQUIREMENTS,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
)


def validate_columns(df) -> bool:
    """
    Check the DataFrame for required and optional columns.
    Computes metric_flags dict → {metric_name: bool} stored in session state.
    Returns True if minimum required columns are present.
    """
    present = set(df.columns)

    missing_required = [c for c in REQUIRED_COLUMNS if c not in present]
    missing_optional = [c for c in OPTIONAL_COLUMNS if c not in present]
    available = [c for c in (REQUIRED_COLUMNS + OPTIONAL_COLUMNS) if c in present]

    st.session_state["available_columns"] = set(available)
    st.session_state["missing_required"] = missing_required
    st.session_state["missing_optional"] = missing_optional

    # --- Compute metric availability flags ---
    metric_flags: dict[str, bool] = {}
    disabled_reasons: dict[str, list[str]] = {}
    for metric_name, required_cols in METRIC_REQUIREMENTS.items():
        missing = [c for c in required_cols if c not in present]
        metric_flags[metric_name] = len(missing) == 0
        if missing:
            disabled_reasons[metric_name] = missing

    st.session_state["metric_flags"] = metric_flags

    # --- Hard block only if Deal ID is missing ---
    if missing_required:
        st.error(
            f"**Missing required column(s):** {', '.join(missing_required)}\n\n"
            "These columns are needed for the dashboard to function. "
            "Please check your data and re-upload."
        )
        return False

    # --- Info banner for disabled metrics ---
    if disabled_reasons:
        with st.expander("ℹ️ Some metrics are disabled due to missing columns", expanded=False):
            for metric, cols in disabled_reasons.items():
                st.markdown(f"- **{metric}** — needs: {', '.join(cols)}")

    # --- Optional columns info ---
    if missing_optional:
        with st.expander("ℹ️ Optional columns not found in your data", expanded=False):
            for col in missing_optional:
                st.markdown(
                    f"- **{col}** — the corresponding filter and charts will be hidden."
                )

    return True
