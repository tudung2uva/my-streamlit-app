"""
Sales Pipeline Analytics Dashboard — V1.5
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
from components.formula_panel import render_formula_panel
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
    concentration_stats,
    get_available_dimensions,
)
from metrics.expansion import expansion_arr_kpi, expansion_over_time_chart
from metrics.pipeline_production import pipeline_production_kpi, pipeline_production_chart
from metrics.reason_lost import reason_lost_chart, reason_lost_table
from metrics.funnel import stage_conversion_funnel
from utils.constants import COL_DEAL_TYPE, COL_DEAL_OWNER, COL_ARR
from utils.helpers import format_currency


# ---------------------------------------------------------------------------
# Benchmark color helpers
# ---------------------------------------------------------------------------
def _color_tag(value_str: str, color: str) -> str:
    """Wrap a metric value string in an HTML span with background color."""
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-weight:600">{value_str}</span>'
    )


def _benchmark_color(metric: str, value: float) -> str:
    """Return hex color based on benchmark thresholds (from render.js)."""
    if metric == "pipeline_coverage":
        if value >= 4.0:
            return "#43A047"  # green
        if value >= 3.0:
            return "#FFA726"  # amber
        return "#E53935"  # red
    if metric in ("count_wr", "rev_wr"):
        if value >= 0.30:
            return "#43A047"
        if value >= 0.15:
            return "#FFA726"
        return "#E53935"
    return "#1E88E5"  # neutral blue


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    st.title("📊 Sales Pipeline Analyzer")

    # ------------------------------------------------------------------ #
    # 1. File Upload
    # ------------------------------------------------------------------ #
    data_loaded = render_upload()
    if not data_loaded:
        st.caption("Upload your sales pipeline data to begin.")
        return

    df = st.session_state["df"]

    # ------------------------------------------------------------------ #
    # 1b. Company Name prompt (one-time, blocking)
    # ------------------------------------------------------------------ #
    if st.session_state.get("company_name") is None:
        st.markdown("---")
        st.subheader("Company Name")
        st.markdown(
            "No single company was auto-detected from the data. "
            "Please enter the company name for this analysis."
        )
        name_input = st.text_input(
            "Company Name",
            key="company_name_input",
            placeholder="e.g. Acme Corp",
        )
        if st.button("✅ Confirm", key="confirm_company"):
            if name_input.strip():
                st.session_state["company_name"] = name_input.strip()
                st.rerun()
            else:
                st.warning("Please enter a company name.")
        st.stop()

    # ------------------------------------------------------------------ #
    # 1c. Metadata bar
    # ------------------------------------------------------------------ #
    company = st.session_state.get("company_name", "")
    import_dt = st.session_state.get("import_datetime")
    file_name = st.session_state.get("file_name", "")
    dt_str = import_dt.strftime("%Y-%m-%d %H:%M") if import_dt else "—"

    st.markdown(
        f"**Company:** {company} &nbsp;|&nbsp; "
        f"**Imported:** {dt_str} &nbsp;|&nbsp; "
        f"**File:** {file_name}"
    )

    # ------------------------------------------------------------------ #
    # 2. Column Validation
    # ------------------------------------------------------------------ #
    valid = validate_columns(df)
    if not valid:
        st.stop()

    flags = st.session_state.get("metric_flags", {})

    # ------------------------------------------------------------------ #
    # 3. Sidebar Filters
    # ------------------------------------------------------------------ #
    filtered_df, time_col = render_sidebar(df)
    currency = st.session_state.get("currency", "€")

    # ------------------------------------------------------------------ #
    # 4. Target ARR input (for Pipeline Coverage)
    # ------------------------------------------------------------------ #
    if flags.get("Pipeline Coverage", False):
        with st.sidebar:
            st.markdown("---")
            st.subheader("Pipeline Target")
            target_arr = st.number_input(
                f"Target ARR ({currency})",
                min_value=0,
                value=1_000_000,
                step=100_000,
                format="%d",
                help="Used to calculate Pipeline Coverage = Open Pipeline / Target",
            )
    else:
        target_arr = 1_000_000

    # ------------------------------------------------------------------ #
    # 5. KPI Cards (Row 1) — with benchmark colors
    # ------------------------------------------------------------------ #
    st.markdown("---")

    # Determine how many KPI cards to show
    kpi_items = []

    if flags.get("Win Rate", False):
        cwr = count_win_rate_kpi(filtered_df)
        kpi_items.append(("Count Win Rate", f"{cwr:.1%}", _benchmark_color("count_wr", cwr)))

    if flags.get("Revenue Win Rate", False):
        rwr = revenue_win_rate_kpi(filtered_df)
        kpi_items.append(("Revenue Win Rate", f"{rwr:.1%}", _benchmark_color("rev_wr", rwr)))

    if flags.get("Pipeline Coverage", False):
        pc = pipeline_coverage_kpi(filtered_df, target_arr)
        kpi_items.append(("Pipeline Coverage", f"{pc:.1f}×", _benchmark_color("pipeline_coverage", pc)))

    if flags.get("Open Pipeline", False):
        oparr = open_pipeline_arr(filtered_df)
        kpi_items.append(("Open Pipeline", format_currency(oparr, currency), "#1E88E5"))

    if flags.get("Sales Cycle", False):
        asc = avg_sales_cycle_kpi(filtered_df)
        kpi_items.append(("Avg Sales Cycle", f"{asc:.0f} days" if asc is not None else "N/A", "#1E88E5"))

    if flags.get("Expansion", False):
        exp_arr = expansion_arr_kpi(filtered_df)
        kpi_items.append(("Expansion ARR", format_currency(exp_arr, currency), "#43A047"))

    if kpi_items:
        cols = st.columns(len(kpi_items))
        for i, (label, val_str, color) in enumerate(kpi_items):
            with cols[i]:
                st.markdown(
                    f"<div style='text-align:center'>"
                    f"<p style='margin:0;font-size:0.85rem;color:#888'>{label}</p>"
                    f"<p style='margin:4px 0 0 0;font-size:1.6rem'>{_color_tag(val_str, color)}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ------------------------------------------------------------------ #
    # 6. Win Rate Over Time (Row 2)
    # ------------------------------------------------------------------ #
    if flags.get("Win Rate", False):
        st.plotly_chart(
            win_rate_over_time_chart(filtered_df, time_col),
            use_container_width=True,
        )

    # ------------------------------------------------------------------ #
    # 7. Pipeline & Sales Cycle side by side (Row 3)
    # ------------------------------------------------------------------ #
    left_chart = flags.get("Open Pipeline", False)
    right_chart = flags.get("Sales Cycle", False)
    if left_chart or right_chart:
        col_left, col_right = st.columns(2)
        if left_chart:
            with col_left:
                st.plotly_chart(pipeline_by_stage_chart(filtered_df), use_container_width=True)
        if right_chart:
            with col_right:
                st.plotly_chart(sales_cycle_histogram(filtered_df), use_container_width=True)

    # ------------------------------------------------------------------ #
    # 8. Pipeline Waterfall (Row 3b)
    # ------------------------------------------------------------------ #
    if flags.get("Open Pipeline", False):
        st.plotly_chart(pipeline_waterfall_chart(filtered_df), use_container_width=True)

    # ------------------------------------------------------------------ #
    # 9. Expansion ARR Over Time
    # ------------------------------------------------------------------ #
    if flags.get("Expansion", False):
        st.plotly_chart(
            expansion_over_time_chart(filtered_df, time_col),
            use_container_width=True,
        )

    # ------------------------------------------------------------------ #
    # 10. Pipeline Production
    # ------------------------------------------------------------------ #
    if flags.get("Pipeline Production", False):
        st.markdown("---")
        st.subheader("📈 Pipeline Production")
        pp_kpi = pipeline_production_kpi(filtered_df)
        st.metric("New Pipeline ARR", format_currency(pp_kpi, currency))
        st.plotly_chart(
            pipeline_production_chart(filtered_df, time_col),
            use_container_width=True,
        )

    # ------------------------------------------------------------------ #
    # 11. Conversion Funnel
    # ------------------------------------------------------------------ #
    if flags.get("Funnel", False):
        st.markdown("---")
        st.subheader("🔻 Conversion Funnel")
        st.plotly_chart(
            stage_conversion_funnel(filtered_df),
            use_container_width=True,
        )

    # ------------------------------------------------------------------ #
    # 12. Sales Cycle Breakdown (Row 4)
    # ------------------------------------------------------------------ #
    if flags.get("Sales Cycle", False):
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
    # 13. Reason Lost Analysis
    # ------------------------------------------------------------------ #
    if flags.get("Reason Lost", False):
        st.markdown("---")
        st.subheader("❌ Reason Lost Analysis")
        col_rl_chart, col_rl_table = st.columns([1, 1])
        with col_rl_chart:
            st.plotly_chart(reason_lost_chart(filtered_df), use_container_width=True)
        with col_rl_table:
            rl_tbl = reason_lost_table(filtered_df)
            if rl_tbl is not None:
                fmt_tbl = rl_tbl.copy()
                if "ARR Lost" in fmt_tbl.columns:
                    fmt_tbl["ARR Lost"] = fmt_tbl["ARR Lost"].apply(
                        lambda x: format_currency(x, currency, short=False)
                    )
                    fmt_tbl["% of Total"] = fmt_tbl["% of Total"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(fmt_tbl, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------ #
    # 14. Concentration Analysis (Row 5)
    # ------------------------------------------------------------------ #
    if flags.get("Concentration", False):
        dims = get_available_dimensions(filtered_df)
        if dims:
            st.markdown("---")
            st.subheader("📊 Concentration Analysis")
            for dim in dims:
                with st.expander(f"Concentration by **{dim['label']}**", expanded=False):
                    # Top-N stats
                    stats = concentration_stats(filtered_df, dim["column"])
                    if stats:
                        label_color = {"Diversified": "#43A047", "Moderate": "#FFA726", "Concentrated": "#E53935"}
                        sc = label_color.get(stats["label"], "#888")
                        st.markdown(
                            f"**#1:** {stats['top_1_pct']:.1f}% &nbsp;|&nbsp; "
                            f"**Top 3:** {stats['top_3_pct']:.1f}% &nbsp;|&nbsp; "
                            f"**Top 10:** {stats['top_10_pct']:.1f}% &nbsp;|&nbsp; "
                            f"{_color_tag(stats['label'], sc)}",
                            unsafe_allow_html=True,
                        )

                    chart = concentration_bar_chart(
                        filtered_df, dim["column"], dim["label"]
                    )
                    st.plotly_chart(chart, use_container_width=True)

                    tbl = concentration_table(filtered_df, dim["column"])
                    if tbl is not None:
                        fmt_tbl = tbl.copy()
                        fmt_tbl["Total ARR"] = fmt_tbl["Total ARR"].apply(
                            lambda x: format_currency(x, currency, short=False)
                        )
                        fmt_tbl["% of Total"] = fmt_tbl["% of Total"].apply(lambda x: f"{x:.1f}%")
                        st.dataframe(fmt_tbl, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------ #
    # 15. Formula Inspector
    # ------------------------------------------------------------------ #
    st.markdown("---")
    render_formula_panel(filtered_df, time_col)

    # ------------------------------------------------------------------ #
    # 16. Raw Data Explorer
    # ------------------------------------------------------------------ #
    with st.expander("🔍 View Filtered Data", expanded=False):
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered_df):,} of {len(df):,} total deals.")


if __name__ == "__main__":
    main()
