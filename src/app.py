"""
Sales Pipeline Analytics Dashboard
Entry point: streamlit run src/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Sales Pipeline Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Imports (after set_page_config which must be the first Streamlit call)
# ---------------------------------------------------------------------------
from components.upload import render_upload
from components.warnings import validate_columns
from components.sidebar import render_sidebar
from metrics.win_rate import (
    count_win_rate_kpi,
    revenue_win_rate_kpi,
    win_rate_over_time_chart,
)
from metrics.pipeline import (
    pipeline_coverage_kpi,
    open_pipeline_arr,
    pipeline_by_stage_chart,
    pipeline_waterfall_chart,
)
from metrics.sales_cycle import (
    avg_sales_cycle_kpi,
    median_sales_cycle_kpi,
    sales_cycle_histogram,
    sales_cycle_by_dimension,
)
from metrics.concentration import (
    concentration_bar_chart,
    concentration_table,
    get_available_dimensions,
)
from utils.constants import COL_DEAL_TYPE, COL_DEAL_OWNER


def main():
    st.title("📊 Sales Pipeline Analyzer")
    st.caption("Upload your sales pipeline data and explore interactive metrics & charts.")

    # ------------------------------------------------------------------ #
    # 1. File Upload
    # ------------------------------------------------------------------ #
    data_loaded = render_upload()
    if not data_loaded:
        return

    df = st.session_state["df"]

    # ------------------------------------------------------------------ #
    # 2. Column Validation
    # ------------------------------------------------------------------ #
    valid = validate_columns(df)
    if not valid:
        st.stop()

    # ------------------------------------------------------------------ #
    # 3. Sidebar Filters
    # ------------------------------------------------------------------ #
    filtered_df, time_col = render_sidebar(df)

    # ------------------------------------------------------------------ #
    # 4. Target ARR input (for Pipeline Coverage)
    # ------------------------------------------------------------------ #
    with st.sidebar:
        st.markdown("---")
        st.subheader("Pipeline Target")
        target_arr = st.number_input(
            "Target ARR ($)",
            min_value=0,
            value=1_000_000,
            step=100_000,
            format="%d",
            help="Used to calculate Pipeline Coverage = Open Pipeline / Target",
        )

    # ------------------------------------------------------------------ #
    # 5. KPI Cards (Row 1)
    # ------------------------------------------------------------------ #
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    cwr = count_win_rate_kpi(filtered_df)
    rwr = revenue_win_rate_kpi(filtered_df)
    pc = pipeline_coverage_kpi(filtered_df, target_arr)
    oparr = open_pipeline_arr(filtered_df)
    asc = avg_sales_cycle_kpi(filtered_df)

    kpi1.metric("Count Win Rate", f"{cwr:.1%}")
    kpi2.metric("Revenue Win Rate", f"{rwr:.1%}")
    kpi3.metric("Pipeline Coverage", f"{pc:.1f}×")
    kpi4.metric("Open Pipeline", f"${oparr:,.0f}")
    kpi5.metric("Avg Sales Cycle", f"{asc:.0f} days" if asc is not None else "N/A")

    # ------------------------------------------------------------------ #
    # 6. Win Rate Over Time (Row 2)
    # ------------------------------------------------------------------ #
    st.plotly_chart(
        win_rate_over_time_chart(filtered_df, time_col),
        use_container_width=True,
    )

    # ------------------------------------------------------------------ #
    # 7. Pipeline & Sales Cycle side by side (Row 3)
    # ------------------------------------------------------------------ #
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(pipeline_by_stage_chart(filtered_df), use_container_width=True)
    with col_right:
        st.plotly_chart(sales_cycle_histogram(filtered_df), use_container_width=True)

    # ------------------------------------------------------------------ #
    # 8. Pipeline Waterfall (Row 3b)
    # ------------------------------------------------------------------ #
    st.plotly_chart(pipeline_waterfall_chart(filtered_df), use_container_width=True)

    # ------------------------------------------------------------------ #
    # 9. Sales Cycle Breakdown (Row 4)
    # ------------------------------------------------------------------ #
    sc_dims = []
    if COL_DEAL_TYPE in filtered_df.columns:
        sc_dims.append((COL_DEAL_TYPE, "Deal Type"))
    if COL_DEAL_OWNER in filtered_df.columns:
        sc_dims.append((COL_DEAL_OWNER, "Deal Owner"))

    if sc_dims:
        cols = st.columns(len(sc_dims))
        for i, (col_name, label) in enumerate(sc_dims):
            with cols[i]:
                st.plotly_chart(
                    sales_cycle_by_dimension(filtered_df, col_name, label),
                    use_container_width=True,
                )

    # ------------------------------------------------------------------ #
    # 10. Concentration Analysis (Row 5)
    # ------------------------------------------------------------------ #
    dims = get_available_dimensions(filtered_df)
    if dims:
        st.markdown("---")
        st.subheader("📊 Concentration Analysis")
        for dim in dims:
            with st.expander(f"Concentration by **{dim['label']}**", expanded=False):
                chart = concentration_bar_chart(
                    filtered_df, dim["column"], dim["label"]
                )
                st.plotly_chart(chart, use_container_width=True)

                tbl = concentration_table(filtered_df, dim["column"])
                if tbl is not None:
                    fmt_tbl = tbl.copy()
                    fmt_tbl["Total ARR"] = fmt_tbl["Total ARR"].apply(lambda x: f"${x:,.0f}")
                    fmt_tbl["% of Total"] = fmt_tbl["% of Total"].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(fmt_tbl, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------ #
    # 11. Raw Data Explorer
    # ------------------------------------------------------------------ #
    st.markdown("---")
    with st.expander("🔍 View Filtered Data", expanded=False):
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered_df):,} of {len(df):,} total deals.")


if __name__ == "__main__":
    main()
