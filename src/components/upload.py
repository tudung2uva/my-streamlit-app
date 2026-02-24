"""
File upload component with clear/replace functionality.
Stores parsed DataFrame in session state for per-user independence.
"""

import streamlit as st
from utils.helpers import load_and_parse


def render_upload() -> bool:
    """
    Render the file uploader. Returns True if data is loaded in session state.
    Handles clear & re-upload flow.
    """
    # If data already loaded, offer a clear button
    if "df" in st.session_state and st.session_state["df"] is not None:
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            n = len(st.session_state["df"])
            st.success(f"✅ Data loaded — **{n:,}** deals from **{st.session_state.get('file_name', 'file')}**")
        with col_btn:
            if st.button("🗑️ Clear & Upload New File", type="secondary"):
                _clear_session()
                st.rerun()
        return True

    # No data — show uploader
    st.markdown("### Upload Sales Pipeline Data")
    st.markdown(
        "Upload a **CSV** or **Excel** file containing your sales pipeline data. "
        "The app will auto-detect delimiters, date formats, and number formats."
    )

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls"],
        key="file_uploader",
        help="Accepted formats: .csv (comma or semicolon separated), .xlsx, .xls",
    )

    if uploaded_file is not None:
        try:
            with st.spinner("Parsing file…"):
                df = load_and_parse(uploaded_file)
            st.session_state["df"] = df
            st.session_state["file_name"] = uploaded_file.name
            st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return False

    # Show instructions while waiting for upload
    st.info(
        "📋 **Expected columns** (minimum): Deal ID, Deal Creation Date, "
        "ARR Amount, Deal Stage, Deal Close Date, Deal Owner, Deal Type.\n\n"
        "Optional columns (enable more filters/metrics): Industry, Region/Country, "
        "Product Tier, Pipeline, Sales Channel, Customer Name, ARR per 1/1, "
        "Churn ARR, Churn Date."
    )
    return False


def _clear_session():
    """Remove all analysis-related keys from session state."""
    keys_to_remove = [
        "df",
        "file_name",
        "available_columns",
        "missing_required",
        "missing_optional",
    ]
    for key in keys_to_remove:
        st.session_state.pop(key, None)
    # Also clear any filter keys
    for key in list(st.session_state.keys()):
        if key.startswith("filter_"):
            del st.session_state[key]
