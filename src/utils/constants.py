"""
Canonical column schema for Sales Pipeline MVP.
Defines required/optional columns, alias mappings for alternate datasets,
and filter configuration.
"""

# ---------------------------------------------------------------------------
# Canonical column names (match Sales MVP.csv)
# ---------------------------------------------------------------------------
COL_DEAL_ID = "Deal ID"
COL_CREATION_DATE = "Deal Creation Date"
COL_ARR = "ARR Amount"
COL_PRODUCT_TIER = "Product / Product Tier"
COL_DEAL_STAGE = "Deal Stage"
COL_CLOSE_DATE = "Deal Close Date"
COL_DEAL_OWNER = "Deal Owner"
COL_PIPELINE = "Pipeline"
COL_DEAL_TYPE = "Deal Type"
COL_INDUSTRY = "Industry"
COL_REGION = "Region/Country"
COL_REASON_LOST = "Reason Lost"
COL_CUSTOMER_NAME = "Customer Name"
COL_ARR_START = "ARR per 1/1"
COL_CHURN_ARR = "Churn ARR"
COL_CHURN_DATE = "Churn Date"
COL_CUSTOMER_OWNER = "Customer Owner"
COL_CHANNEL = "Deal Source / Sales Channel"

# Derived columns (added during parsing)
COL_IS_CLOSED_WON = "_Is Closed Won"
COL_IS_CLOSED_LOST = "_Is Closed Lost"
COL_IS_OPEN = "_Is Open"
COL_FISCAL_YEAR = "_Fiscal Year"
COL_FISCAL_QUARTER = "_Fiscal Quarter"
COL_FISCAL_MONTH = "_Fiscal Month"
COL_FISCAL_WEEK = "_Fiscal Week"
COL_DAYS_TO_CLOSE = "_Days to Close"

# ---------------------------------------------------------------------------
# Required vs Optional columns
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = [
    COL_DEAL_ID,
]

OPTIONAL_COLUMNS = [
    COL_CREATION_DATE,
    COL_ARR,
    COL_DEAL_STAGE,
    COL_CLOSE_DATE,
    COL_DEAL_OWNER,
    COL_DEAL_TYPE,
    COL_PRODUCT_TIER,
    COL_PIPELINE,
    COL_INDUSTRY,
    COL_REGION,
    COL_REASON_LOST,
    COL_CUSTOMER_NAME,
    COL_ARR_START,
    COL_CHURN_ARR,
    COL_CHURN_DATE,
    COL_CUSTOMER_OWNER,
    COL_CHANNEL,
]

# ---------------------------------------------------------------------------
# Metric → required columns (for graceful degradation)
# ---------------------------------------------------------------------------
METRIC_REQUIREMENTS: dict[str, list[str]] = {
    "Win Rate": [COL_DEAL_STAGE, COL_CREATION_DATE],
    "Revenue Win Rate": [COL_DEAL_STAGE, COL_CREATION_DATE, COL_ARR],
    "Pipeline Coverage": [COL_DEAL_STAGE, COL_ARR],
    "Open Pipeline": [COL_DEAL_STAGE, COL_ARR],
    "Sales Cycle": [COL_DEAL_STAGE, COL_CREATION_DATE, COL_CLOSE_DATE],
    "Concentration": [COL_ARR],
    "Expansion": [COL_ARR, COL_DEAL_TYPE],
    "Pipeline Production": [COL_ARR, COL_CREATION_DATE],
    "Reason Lost": [COL_REASON_LOST, COL_DEAL_STAGE],
    "Funnel": [COL_DEAL_STAGE],
    "ACV": [COL_ARR, COL_DEAL_STAGE],
    "Net Revenue Retention": [COL_ARR_START, COL_CHURN_ARR, COL_DEAL_TYPE, COL_ARR],
    "Logo Churn": [COL_CUSTOMER_NAME, COL_CHURN_DATE],
    "ARR Churn": [COL_CHURN_ARR, COL_ARR_START],
}

# ---------------------------------------------------------------------------
# Alias mapping: canonical name → list of known alternate names
# When a dataset uses an alternate name, it gets renamed to canonical.
# ---------------------------------------------------------------------------
COLUMN_ALIASES: dict[str, list[str]] = {
    COL_CREATION_DATE: ["Create Date", "Creation Date", "Deal Create Date", "Created Date"],
    COL_ARR: [
        "Amount in Company Currency",
        "Amount in company currency",
        "Amount",
        "ARR",
        "Annual Revenue",
        "Deal Amount",
        "Revenue",
    ],
    COL_CLOSE_DATE: ["Close Date", "Closing Date", "Deal Closing Date"],
    COL_DEAL_STAGE: ["Stage", "Deal Status", "Status"],
    COL_DEAL_OWNER: ["Owner", "Sales Rep", "Rep", "Account Executive"],
    COL_DEAL_TYPE: ["Deal Type (No blanks)", "Type", "Opportunity Type"],
    COL_CHANNEL: [
        "Channel",
        "Source",
        "Sales Channel",
        "Deal Source",
        "Lead Source",
    ],
    COL_PRODUCT_TIER: ["Product Tier", "Product", "Tier", "Product Name"],
    COL_REGION: ["Region", "Country", "Geography", "Territory"],
    COL_CUSTOMER_NAME: ["Company name", "Company Name", "Account Name", "Customer", "Account"],
    COL_PIPELINE: ["Sales Pipeline"],
    COL_DEAL_ID: ["Opportunity ID", "Opp ID", "ID"],
    COL_ARR_START: ["Starting ARR", "Beginning ARR", "ARR Start"],
    COL_CHURN_ARR: ["Churned ARR", "Lost ARR"],
    COL_CHURN_DATE: ["Churned Date", "Cancel Date"],
    COL_CUSTOMER_OWNER: ["Account Owner", "CSM"],
    COL_REASON_LOST: ["Loss Reason", "Closed Lost Reason", "Reason"],
}

# ---------------------------------------------------------------------------
# Deal stage values (case-insensitive matching applied at runtime)
# ---------------------------------------------------------------------------
STAGE_CLOSED_WON = "Closed Won"
STAGE_CLOSED_LOST = "Closed Lost"

# ---------------------------------------------------------------------------
# Filter configuration
# "single" = st.selectbox, "multi" = st.multiselect
# column=None means this filter is derived (not a direct column)
# ---------------------------------------------------------------------------
FILTER_CONFIG = [
    {
        "key": "time_increment",
        "label": "Time Increment",
        "type": "single",
        "column": None,  # derived: used to pick grouping level
        "options": ["Year", "Quarter", "Month", "Week"],
        "default": "Quarter",
    },
    {
        "key": "fiscal_year",
        "label": "Fiscal Year",
        "type": "multi",
        "column": COL_FISCAL_YEAR,
        "depends_on": COL_CREATION_DATE,  # always available if creation date exists
    },
    {
        "key": "deal_type",
        "label": "Deal Type",
        "type": "multi",
        "column": COL_DEAL_TYPE,
        "depends_on": COL_DEAL_TYPE,
    },
    {
        "key": "deal_owner",
        "label": "Sales Rep",
        "type": "multi",
        "column": COL_DEAL_OWNER,
        "depends_on": COL_DEAL_OWNER,
    },
    {
        "key": "pipeline",
        "label": "Pipeline",
        "type": "multi",
        "column": COL_PIPELINE,
        "depends_on": COL_PIPELINE,
    },
    {
        "key": "industry",
        "label": "Industry",
        "type": "multi",
        "column": COL_INDUSTRY,
        "depends_on": COL_INDUSTRY,
    },
    {
        "key": "region",
        "label": "Region / Country",
        "type": "multi",
        "column": COL_REGION,
        "depends_on": COL_REGION,
    },
    {
        "key": "product_tier",
        "label": "Product Tier",
        "type": "multi",
        "column": COL_PRODUCT_TIER,
        "depends_on": COL_PRODUCT_TIER,
    },
    {
        "key": "channel",
        "label": "Sales Channel",
        "type": "multi",
        "column": COL_CHANNEL,
        "depends_on": COL_CHANNEL,
    },
]

# ---------------------------------------------------------------------------
# Legacy alias (kept for reference, superseded by METRIC_REQUIREMENTS above)
# ---------------------------------------------------------------------------
# METRIC_DEPENDENCIES = { ... }

# Concentration dimension columns – each shown if present
CONCENTRATION_DIMENSIONS = [
    {"column": COL_REGION, "label": "Region / Country"},
    {"column": COL_DEAL_OWNER, "label": "Deal Owner"},
    {"column": COL_INDUSTRY, "label": "Industry"},
    {"column": COL_PRODUCT_TIER, "label": "Product Tier"},
    {"column": COL_PIPELINE, "label": "Pipeline (Open deals)"},
    {"column": COL_CUSTOMER_NAME, "label": "Customer"},
]
