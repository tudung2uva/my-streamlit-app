"""
Column validation: compare uploaded DataFrame against the canonical schema.
Shows errors for missing required columns and warnings for missing optional columns.
"""

import streamlit as st

from utils.constants import (
    METRIC_DEPENDENCIES,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
)


def validate_columns(df) -> bool:
    """
    Check the DataFrame for required and optional columns.
    Stores results in session state.
    Returns True if all required columns are present (dashboard can render).
    """
    present = set(df.columns)

    missing_required = [c for c in REQUIRED_COLUMNS if c not in present]
    missing_optional = [c for c in OPTIONAL_COLUMNS if c not in present]
    available = [c for c in (REQUIRED_COLUMNS + OPTIONAL_COLUMNS) if c in present]

    st.session_state["available_columns"] = set(available)
    st.session_state["missing_required"] = missing_required
    st.session_state["missing_optional"] = missing_optional

    # --- Required column errors ---
    if missing_required:
        st.error(
            f"**Missing required column(s):** {', '.join(missing_required)}\n\n"
            "These columns are needed for core metrics. "
            "Please check your data and re-upload."
        )
        # Show which metrics are affected
        affected: list[str] = []
        for metric, deps in METRIC_DEPENDENCIES.items():
            if any(d in missing_required for d in deps):
                affected.append(metric)
        if affected:
            st.warning(
                f"**Metrics unavailable** due to missing columns: {', '.join(affected)}"
            )
        return False

    # --- Optional column warnings ---
    if missing_optional:
        with st.expander("ℹ️ Optional columns not found in your data", expanded=False):
            for col in missing_optional:
                st.markdown(f"- **{col}** — the corresponding filter and concentration chart will be hidden.")

    return True
