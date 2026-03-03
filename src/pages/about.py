import streamlit as st

def about():
    st.title("About Sales Pipeline Analyzer")
    st.write("""
        This application provides a practical operating view of sales-pipeline performance,
        conversion, and ARR composition.

        ## Scope
        - Deal-level KPI monitoring
        - Time-based trend analysis (Year / Quarter / Month / Week)
        - Pipeline quality and concentration diagnostics
        - Expansion and reason-lost analysis

        ## Metric Governance
        - Formulas are exposed in **Formula Definitions & Computation Detail**
        - A dedicated **Metric Dictionary** section provides metric logic and required columns
        - Missing columns gracefully disable dependent metrics instead of failing the dashboard

        ## Intended Audience
        Revenue Operations, Sales Leadership, and Finance stakeholders who need a
        concise but auditable picture of pipeline health.
    """)

if __name__ == "__main__":
    about()