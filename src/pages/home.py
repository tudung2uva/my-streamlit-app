import streamlit as st

def home():
    st.title("Sales Pipeline Analyzer")
    st.write("A focused dashboard for pipeline quality, conversion efficiency, and revenue mix.")

    st.header("What You Can Monitor")
    st.write("- Win-rate quality (count and revenue weighted)")
    st.write("- Pipeline sufficiency versus target ARR")
    st.write("- Sales cycle speed and consistency")
    st.write("- Concentration risk by customer, region, owner, and industry")
    st.write("- Expansion contribution (upsell and cross-sell)")

    st.header("How to Use")
    st.write("1. Upload a CSV or Excel pipeline export.")
    st.write("2. Configure fiscal-year start, time increment, and filters in the sidebar.")
    st.write("3. Review KPI cards, trend charts, and segment breakdowns.")
    st.write("4. Open **Metric Dictionary** for formulas and required columns.")

    st.header("Data Requirements")
    st.write("- Required: Deal ID")
    st.write("- Recommended: Deal Stage, Deal Creation Date, ARR Amount, Deal Close Date")
    st.write("- Optional dimensions unlock extra filters and concentration views")
    
if __name__ == "__main__":
    home()