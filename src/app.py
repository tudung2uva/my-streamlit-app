"""
Sales Pipeline Analytics Dashboard — V2.0
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
    pipeline_coverage_stats,
    pipeline_coverage_detail_table,
    open_pipeline_arr,
    pipeline_by_stage_chart,
    pipeline_waterfall_chart,
)
from metrics.sales_cycle import (
    avg_sales_cycle_kpi,
    median_sales_cycle_kpi,
    sales_cycle_histogram,
    sales_cycle_by_dimension,
    sales_cycle_detail_table,
)
from metrics.concentration import (
    concentration_bar_chart,
    concentration_table,
    concentration_stats,
    get_available_dimensions,
)
from metrics.expansion import expansion_arr_kpi, expansion_over_time_chart
from metrics.pipeline_production import (
    pipeline_production_kpi,
    pipeline_production_chart,
    pipeline_production_stats,
    pipeline_production_detail_table,
)
from metrics.reason_lost import reason_lost_chart, reason_lost_table
from metrics.funnel import stage_conversion_funnel
from metrics.acv import acv_kpi, acv_over_time_chart, acv_detail_table
from metrics.nrr import nrr_kpi, nrr_over_time_chart, nrr_detail_table
from metrics.churn import (
    logo_churn_kpi,
    logo_churn_over_time_chart,
    logo_churn_detail_table,
    arr_churn_kpi,
    arr_churn_over_time_chart,
    arr_churn_detail_table,
)

from utils.constants import COL_DEAL_TYPE, COL_DEAL_OWNER, COL_ARR
from utils.helpers import format_currency


# ---------------------------------------------------------------------------
# Benchmark color helpers
# ---------------------------------------------------------------------------
def _color_tag(value_str: str, color: str) -> str:
    """Wrap a metric value string in a colored, bold style."""
    return (
        f'<span style="color:{color};font-weight:650;letter-spacing:0.2px">{value_str}</span>'
    )


def _benchmark_color(metric: str, value: float) -> str:
    """Return hex color based on benchmark thresholds."""
    if metric == "pipeline_coverage":
        if value >= 4.0:
            return "#43A047"
        if value >= 3.0:
            return "#FFA726"
        return "#E53935"
    if metric in ("count_wr", "rev_wr"):
        if value >= 0.30:
            return "#43A047"
        if value >= 0.15:
            return "#FFA726"
        return "#E53935"
    if metric == "nrr":
        if value >= 1.0:
            return "#43A047"
        if value >= 0.90:
            return "#FFA726"
        return "#E53935"
    if metric in ("logo_churn", "arr_churn"):
        if value <= 0.05:
            return "#43A047"
        if value <= 0.15:
            return "#FFA726"
        return "#E53935"
    return "#1E88E5"


# ---------------------------------------------------------------------------
# Render KPI row helper
# ---------------------------------------------------------------------------
def _render_kpi_row(kpi_items: list[tuple[str, str, str]]) -> None:
    """Render a row of KPI cards."""
    if not kpi_items:
        return
    cols = st.columns(len(kpi_items))
    for i, (label, val_str, color) in enumerate(kpi_items):
        with cols[i]:
            st.markdown(
                f"<div class='kpi-card' style='text-align:center'>"
                f"<p style='margin:0;font-size:0.85rem;color:#888'>{label}</p>"
                f"<p style='margin:4px 0 0 0;font-size:1.6rem'>{_color_tag(val_str, color)}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: "Segoe UI", "Inter", "IBM Plex Sans", sans-serif;
        }
        .kpi-card {
            border: 1px solid #d8dde6;
            border-radius: 8px;
            padding: 10px 8px;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
    fy_start = st.session_state.get("_fy_start_month", 1)

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
    # 4b. Formula Definitions (top)
    # ------------------------------------------------------------------ #
    st.markdown("---")
    render_formula_panel(filtered_df, time_col)

    # ================================================================== #
    #  KPI SUMMARY ROW
    # ================================================================== #
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
        msc = median_sales_cycle_kpi(filtered_df)
        kpi_items.append(("Avg Sales Cycle", f"{asc:.0f} d" if asc is not None else "N/A", "#1E88E5"))
        kpi_items.append(("Median Sales Cycle", f"{msc:.0f} d" if msc is not None else "N/A", "#1E88E5"))

    if flags.get("ACV", False):
        acv_val = acv_kpi(filtered_df)
        kpi_items.append(("ACV", format_currency(acv_val, currency), "#1E88E5"))

    if flags.get("Expansion", False):
        exp_arr = expansion_arr_kpi(filtered_df)
        kpi_items.append(("Expansion ARR", format_currency(exp_arr, currency), "#43A047"))

    if flags.get("Net Revenue Retention", False):
        nrr_val = nrr_kpi(filtered_df)
        kpi_items.append(("NRR", f"{nrr_val:.1%}", _benchmark_color("nrr", nrr_val)))

    if flags.get("Logo Churn", False):
        _, _, lc_pct = logo_churn_kpi(filtered_df)
        kpi_items.append(("Logo Churn", f"{lc_pct:.1%}", _benchmark_color("logo_churn", lc_pct)))

    if flags.get("ARR Churn", False):
        _, _, ac_pct = arr_churn_kpi(filtered_df)
        kpi_items.append(("ARR Churn", f"{ac_pct:.1%}", _benchmark_color("arr_churn", ac_pct)))

    if kpi_items:
        st.markdown("---")
        # Split into rows of max 6 to avoid cramping
        ROW_SIZE = 6
        for start in range(0, len(kpi_items), ROW_SIZE):
            _render_kpi_row(kpi_items[start : start + ROW_SIZE])

    # ================================================================== #
    #  GROUPED SECTIONS (expandable)
    # ================================================================== #

    # ------------------------------------------------------------------ #
    # A. Win Rate & Conversion Funnel
    # ------------------------------------------------------------------ #
    has_wr = flags.get("Win Rate", False)
    has_funnel = flags.get("Funnel", False)
    if has_wr or has_funnel:
        st.markdown("---")
        with st.expander("📈 Win Rate & Conversion Funnel", expanded=True):
            if has_wr:
                st.plotly_chart(
                    win_rate_over_time_chart(filtered_df, time_col),
                    use_container_width=True,
                )
            if has_funnel:
                st.plotly_chart(
                    stage_conversion_funnel(filtered_df),
                    use_container_width=True,
                )

    # ------------------------------------------------------------------ #
    # B. Pipeline & Coverage
    # ------------------------------------------------------------------ #
    has_pipeline = flags.get("Open Pipeline", False)
    has_coverage = flags.get("Pipeline Coverage", False)
    has_production = flags.get("Pipeline Production", False)
    if has_pipeline or has_coverage or has_production:
        st.markdown("---")
        with st.expander("🔷 Pipeline & Coverage", expanded=True):
            # Pipeline by Stage + ARR Breakdown side by side
            if has_pipeline:
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(pipeline_by_stage_chart(filtered_df), use_container_width=True)
                with c2:
                    st.plotly_chart(pipeline_waterfall_chart(filtered_df), use_container_width=True)

            # Coverage detail table
            if has_coverage:
                cov_tbl = pipeline_coverage_detail_table(filtered_df, target_arr, time_col)
                if cov_tbl is not None:
                    st.markdown("**Pipeline Coverage by Period**")
                    fmt = cov_tbl.copy()
                    for c in ["Open Pipeline ARR", "Target ARR", "Median Deal", "Avg Deal"]:
                        if c in fmt.columns:
                            fmt[c] = fmt[c].apply(lambda x: format_currency(x, currency, short=False))
                    st.dataframe(fmt, use_container_width=True, hide_index=True)

            # Pipeline Production
            if has_production:
                st.markdown("---")
                pp_kpi = pipeline_production_kpi(filtered_df)
                med_pp, avg_pp = pipeline_production_stats(filtered_df)
                kp1, kp2, kp3 = st.columns(3)
                kp1.metric("Total New Pipeline ARR", format_currency(pp_kpi, currency))
                kp2.metric("Median Deal Size", format_currency(med_pp, currency))
                kp3.metric("Avg Deal Size", format_currency(avg_pp, currency))
                st.plotly_chart(
                    pipeline_production_chart(filtered_df, time_col),
                    use_container_width=True,
                )
                pp_tbl = pipeline_production_detail_table(filtered_df, time_col)
                if pp_tbl is not None:
                    fmt = pp_tbl.copy()
                    for c in ["Total Pipeline ARR", "Median Deal ARR", "Avg Deal ARR"]:
                        if c in fmt.columns:
                            fmt[c] = fmt[c].apply(lambda x: format_currency(x, currency, short=False))
                    st.dataframe(fmt, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------ #
    # C. Sales Cycle
    # ------------------------------------------------------------------ #
    if flags.get("Sales Cycle", False):
        st.markdown("---")
        with st.expander("⏱️ Sales Cycle", expanded=True):
            # Histogram
            st.plotly_chart(sales_cycle_histogram(filtered_df), use_container_width=True)

            # Box plots by dimension
            sc_dims = []
            if COL_DEAL_TYPE in filtered_df.columns:
                sc_dims.append((COL_DEAL_TYPE, "Deal Type"))
            if COL_DEAL_OWNER in filtered_df.columns:
                sc_dims.append((COL_DEAL_OWNER, "Deal Owner"))

            if sc_dims:
                dim_cols = st.columns(len(sc_dims))
                for i, (col_name, label) in enumerate(sc_dims):
                    with dim_cols[i]:
                        st.plotly_chart(
                            sales_cycle_by_dimension(filtered_df, col_name, label),
                            use_container_width=True,
                        )

            # Detail table
            sc_tbl = sales_cycle_detail_table(filtered_df, time_col)
            if sc_tbl is not None:
                st.markdown("**Sales Cycle by Period**")
                st.dataframe(sc_tbl, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------ #
    # D. ACV & Expansion
    # ------------------------------------------------------------------ #
    has_acv = flags.get("ACV", False)
    has_expansion = flags.get("Expansion", False)
    if has_acv or has_expansion:
        st.markdown("---")
        with st.expander("💰 ACV & Expansion", expanded=True):
            if has_acv:
                st.plotly_chart(
                    acv_over_time_chart(filtered_df, time_col),
                    use_container_width=True,
                )
                acv_tbl = acv_detail_table(filtered_df, time_col)
                if acv_tbl is not None:
                    fmt = acv_tbl.copy()
                    for c in ["Total ARR Won", "Avg ACV", "Median ACV"]:
                        if c in fmt.columns:
                            fmt[c] = fmt[c].apply(lambda x: format_currency(x, currency, short=False))
                    st.dataframe(fmt, use_container_width=True, hide_index=True)

            if has_expansion:
                if has_acv:
                    st.markdown("---")
                st.plotly_chart(
                    expansion_over_time_chart(filtered_df, time_col),
                    use_container_width=True,
                )

    # ------------------------------------------------------------------ #
    # E. Retention & Churn
    # ------------------------------------------------------------------ #
    has_nrr = flags.get("Net Revenue Retention", False)
    has_logo_churn = flags.get("Logo Churn", False)
    has_arr_churn = flags.get("ARR Churn", False)
    if has_nrr or has_logo_churn or has_arr_churn:
        st.markdown("---")
        with st.expander("🔄 Retention & Churn", expanded=True):
            # --- NRR ---
            if has_nrr:
                nrr_val = nrr_kpi(filtered_df)
                st.markdown(
                    f"**Net Revenue Retention:** {_color_tag(f'{nrr_val:.1%}', _benchmark_color('nrr', nrr_val))}",
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    nrr_over_time_chart(filtered_df, time_col, fy_start),
                    use_container_width=True,
                )
                nrr_tbl = nrr_detail_table(filtered_df, time_col, fy_start)
                if nrr_tbl is not None:
                    fmt = nrr_tbl.copy()
                    for c in ["Starting ARR", "Expansion ARR", "Churn ARR", "Ending ARR"]:
                        if c in fmt.columns:
                            fmt[c] = fmt[c].apply(lambda x: format_currency(x, currency, short=False))
                    fmt["NRR %"] = fmt["NRR %"].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(fmt, use_container_width=True, hide_index=True)

            # --- Logo Churn ---
            if has_logo_churn:
                if has_nrr:
                    st.markdown("---")
                churned, starting, lc_pct = logo_churn_kpi(filtered_df)
                k1, k2, k3 = st.columns(3)
                k1.metric("Starting Customers", f"{starting:,}")
                k2.metric("Churned Customers", f"{churned:,}")
                k3.metric("Logo Churn Rate", f"{lc_pct:.1%}")
                st.plotly_chart(
                    logo_churn_over_time_chart(filtered_df, time_col, fy_start),
                    use_container_width=True,
                )
                lc_tbl = logo_churn_detail_table(filtered_df, time_col, fy_start)
                if lc_tbl is not None:
                    fmt = lc_tbl.copy()
                    fmt["Logo Churn %"] = fmt["Logo Churn %"].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(fmt, use_container_width=True, hide_index=True)

            # --- ARR Churn ---
            if has_arr_churn:
                if has_nrr or has_logo_churn:
                    st.markdown("---")
                churn_arr_val, start_arr_val, ac_pct = arr_churn_kpi(filtered_df)
                k1, k2, k3 = st.columns(3)
                k1.metric("Starting ARR", format_currency(start_arr_val, currency))
                k2.metric("Churn ARR", format_currency(churn_arr_val, currency))
                k3.metric("ARR Churn Rate", f"{ac_pct:.1%}")
                st.plotly_chart(
                    arr_churn_over_time_chart(filtered_df, time_col, fy_start),
                    use_container_width=True,
                )
                ac_tbl = arr_churn_detail_table(filtered_df, time_col, fy_start)
                if ac_tbl is not None:
                    fmt = ac_tbl.copy()
                    for c in ["Starting ARR", "Churn ARR"]:
                        if c in fmt.columns:
                            fmt[c] = fmt[c].apply(lambda x: format_currency(x, currency, short=False))
                    fmt["ARR Churn %"] = fmt["ARR Churn %"].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(fmt, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------ #
    # F. Reason Lost
    # ------------------------------------------------------------------ #
    if flags.get("Reason Lost", False):
        st.markdown("---")
        with st.expander("❌ Reason Lost Analysis", expanded=False):
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
    # G. Concentration Analysis
    # ------------------------------------------------------------------ #
    if flags.get("Concentration", False):
        dims = get_available_dimensions(filtered_df)
        if dims:
            st.markdown("---")
            with st.expander("📊 Concentration Analysis", expanded=False):
                for dim in dims:
                    st.markdown(f"**Concentration by {dim['label']}**")
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
                    st.markdown("---")

    # ------------------------------------------------------------------ #
    # H. Raw Data Explorer
    # ------------------------------------------------------------------ #
    with st.expander("🔍 View Filtered Data", expanded=False):
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered_df):,} of {len(df):,} total deals.")


if __name__ == "__main__":
    main()
