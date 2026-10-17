from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

from data_loader import load_holdings

from analysis import (
    calculate_stock_exposure,
    calculate_fund_overlap,
    calculate_sector_exposure,
    calculate_overlap_details,
    generate_concentration_alerts,
)

from parser import (
    extract_pdf_text,
    parse_cas_schemes,
    match_scheme_to_fund,
)

# Change this if your weight column in holdings has a different name
WEIGHT_COLUMN = "weight"

# Real holdings built from AMC disclosures with build_holdings.py
LIBRARY_PATH = Path(__file__).with_name("holdings_library.csv")
OTHER_PREFIX = "Other holdings (non-equity)"
OTHER_SECTOR = "Other / Cash & Debt"

# ---------------------------------------------------------------
# Design system (muted dark green-charcoal, ivory text, brass accents)
# ---------------------------------------------------------------
BG = "#1E2622"          # page background
PANEL = "#273029"       # cards, sidebar
PANEL_ALT = "#2F3A32"   # hover / inputs
IVORY = "#EDE6D3"       # primary text
MUTED = "#A9A793"       # secondary text
BRASS = "#C2A560"       # accent
SAGE = "#7F9482"
CLARET = "#C0675A"      # alert accent
LINE = "rgba(194, 165, 96, 0.28)"

CHART_COLORS = [
    "#C2A560", "#7F9482", "#B5675B", "#5E7C6B",
    "#A58A6B", "#8497A6", "#D8C58A", "#8A6F5C",
    "#9DB0A0", "#C98F7F", "#6C8796", "#B9AE8A",
]

SERIF = "'Cormorant Garamond', Georgia, 'Times New Roman', serif"
SANS = "'Inter', 'Helvetica Neue', Arial, sans-serif"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,400;1,500&family=Inter:wght@400;500;600&display=swap');

html, body, .stApp, p, li, label, span, div {{
    font-family: {SANS};
    color: {IVORY};
}}

.stApp {{ background-color: {BG}; }}

/* Keep header but make it blend in (so the sidebar toggle still works) */
header[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer {{ visibility: hidden; }}

.block-container {{
    max-width: 1240px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}}

/* ---------- Top bar ---------- */
.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.4rem 0 1.2rem 0;
    border-bottom: 1px solid {LINE};
    margin-bottom: 1.6rem;
}}
.brand {{
    font-family: {SERIF};
    font-size: 2.3rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    color: {IVORY};
    line-height: 1;
}}
.brand span {{ color: {BRASS}; }}
.badge {{
    display: inline-block;
    margin-left: 0.9rem;
    padding: 0.18rem 0.6rem;
    font-family: {SANS};
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {BRASS};
    border: 1px solid {BRASS};
    vertical-align: middle;
}}
.tagline {{
    font-family: {SERIF};
    font-style: italic;
    font-size: 1.15rem;
    color: {MUTED};
    text-align: right;
    max-width: 420px;
    line-height: 1.3;
}}

/* ---------- Headings ---------- */
h3, [data-testid="stHeading"] h3 {{
    font-family: {SERIF} !important;
    font-weight: 600 !important;
    font-size: 1.7rem !important;
    color: {IVORY} !important;
    letter-spacing: 0.02em;
    margin-top: 1.6rem !important;
}}
.section-note {{
    font-size: 0.9rem;
    color: {MUTED};
    margin: -0.4rem 0 1rem 0;
}}

[data-testid="stCaptionContainer"], .stCaption {{
    color: {MUTED} !important;
    font-size: 0.88rem !important;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background-color: {PANEL};
    border-right: 1px solid {LINE};
}}
section[data-testid="stSidebar"] h2 {{
    font-family: {SERIF} !important;
    font-size: 1.6rem !important;
    color: {IVORY} !important;
}}
.side-label {{
    font-size: 0.7rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {BRASS};
    margin: 1.4rem 0 0.4rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid {LINE};
}}
section[data-testid="stSidebar"] label p {{
    font-size: 0.78rem !important;
    letter-spacing: 0.04em;
    color: {MUTED} !important;
}}

/* ---------- Inputs ---------- */
div[data-baseweb="input"], div[data-baseweb="select"] > div,
div[data-baseweb="base-input"] {{
    background-color: {PANEL_ALT} !important;
    border-radius: 4px !important;
    border-color: {LINE} !important;
}}
div[data-baseweb="input"] input {{ color: {IVORY} !important; }}
div[data-baseweb="input"]:focus-within,
div[data-baseweb="select"] > div:focus-within {{
    border-color: {BRASS} !important;
    box-shadow: none !important;
}}
[data-testid="stNumberInput"] button {{
    background-color: {PANEL_ALT};
    color: {IVORY};
    border-radius: 0;
}}
div[data-baseweb="slider"] div[role="slider"] {{
    background-color: {BRASS} !important;
    border: 2px solid {BG} !important;
    box-shadow: none !important;
}}
[data-testid="stSliderThumbValue"], [data-testid="stTickBarMin"],
[data-testid="stTickBarMax"] {{
    color: {BRASS} !important;
}}

/* ---------- KPI cards ---------- */
[data-testid="stMetric"] {{
    background-color: {PANEL};
    border: 1px solid {LINE};
    border-top: 2px solid {BRASS};
    border-radius: 4px;
    padding: 1.1rem 1.2rem;
}}
[data-testid="stMetricLabel"] p {{
    font-size: 0.68rem !important;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {MUTED} !important;
}}
[data-testid="stMetricValue"] {{
    font-family: {SERIF};
    font-weight: 600;
    font-size: 2.2rem;
    color: {IVORY};
}}

/* ---------- Tabs ---------- */
div[data-baseweb="tab-list"] {{
    gap: 0.4rem;
    border-bottom: 1px solid {LINE};
}}
button[data-baseweb="tab"] {{
    background: transparent;
    padding: 0.8rem 1.4rem;
}}
button[data-baseweb="tab"] p {{
    font-size: 0.78rem !important;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {MUTED} !important;
}}
button[data-baseweb="tab"][aria-selected="true"] p {{
    color: {BRASS} !important;
}}
div[data-baseweb="tab-highlight"] {{ background-color: {BRASS} !important; }}
div[data-baseweb="tab-border"] {{ background-color: transparent !important; }}

/* ---------- Alerts ---------- */
div[data-testid="stAlert"] {{
    background-color: {PANEL} !important;
    border: 1px solid {LINE};
    border-left: 3px solid {CLARET};
    border-radius: 4px;
}}
div[data-testid="stAlert"] p {{
    color: {IVORY} !important;
    font-size: 0.95rem;
}}
div[data-testid="stAlert"] svg {{
    color: {CLARET} !important;
    fill: {CLARET} !important;
}}

/* ---------- Buttons ---------- */
.stDownloadButton button, .stButton button {{
    background-color: transparent;
    color: {BRASS};
    border: 1px solid {BRASS};
    border-radius: 4px;
    font-size: 0.74rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    padding: 0.55rem 1.3rem;
    transition: all 0.2s ease;
}}
.stDownloadButton button:hover, .stButton button:hover {{
    background-color: {BRASS};
    color: {BG};
    border-color: {BRASS};
}}

/* ---------- Tables & charts ---------- */
[data-testid="stDataFrame"] {{
    border: 1px solid {LINE};
    border-radius: 4px;
}}
[data-testid="stPlotlyChart"] {{
    background-color: {PANEL};
    border: 1px solid {LINE};
    border-radius: 4px;
    padding: 0.5rem;
}}

/* ---------- Footer ---------- */
.colophon {{
    text-align: center;
    margin-top: 3.5rem;
    padding-top: 1.3rem;
    border-top: 1px solid {LINE};
    font-size: 0.8rem;
    color: {MUTED};
    line-height: 1.7;
}}
</style>
"""


def style_figure(fig, height=None):
    """Apply the house style to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=SANS, color=IVORY, size=13),
        title=dict(
            font=dict(family=SERIF, size=22, color=IVORY),
            x=0.02,
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            font=dict(family=SANS, size=12, color=IVORY),
            bgcolor="rgba(0,0,0,0)",
        ),
        colorway=CHART_COLORS,
    )
    if height:
        fig.update_layout(height=height)
    return fig


def calculate_investment_overlap(holdings, investments, weight_col=WEIGHT_COLUMN):
    """Calculate shared stock exposure in rupees for each fund pair."""
    active = {fund: amount for fund, amount in investments.items() if amount > 0}
    if not active:
        return pd.DataFrame()

    weights = holdings.pivot_table(
        index="fund",
        columns="stock",
        values=weight_col,
        aggfunc="sum",
        fill_value=0.0,
    ).reindex(list(active.keys()), fill_value=0.0)

    # Dataset weights are fractions (e.g. 0.40), not percentages (40).
    weight_totals = weights.sum(axis=1)
    if not ((weight_totals - 1.0).abs() < 1e-6).all():
        raise ValueError(
            "Every selected fund must have complete stock weights that sum to 100%."
        )

    amounts = pd.Series(active, dtype=float).reindex(weights.index)
    rupee_exposure = weights.mul(amounts, axis=0)

    funds = rupee_exposure.index
    matrix = pd.DataFrame(0.0, index=funds, columns=funds)
    for fund_a in funds:
        for fund_b in funds:
            shared_exposure = pd.concat(
                [rupee_exposure.loc[fund_a], rupee_exposure.loc[fund_b]],
                axis=1,
            ).min(axis=1)
            matrix.loc[fund_a, fund_b] = shared_exposure.sum()

    return matrix


def reset_pdf_state():
    """Forget the previous PDF and its widget values."""
    for index in range(len(st.session_state.get("pdf_schemes", []))):
        st.session_state.pop(f"pdf_amt_{index}", None)
    st.session_state["pdf_text"] = ""
    st.session_state["pdf_schemes"] = []
    st.session_state["pdf_file_sig"] = ""


# ------------------------------------------------------------------
# Page setup and data
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Portfolio X-Ray",
    page_icon="📊",
    layout="wide",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def load_sample_holdings_safely():
    """
    Use data_loader.load_holdings(); if it fails (for example because a numeric
    column was read as text), fall back to reading sample_holdings.csv directly
    and clean the numbers. Returns (DataFrame, notice or None).
    """
    try:
        return load_holdings(), None
    except Exception as loader_error:
        base = Path(__file__).parent
        candidates = []
        for folder in (base, base / "data", base.parent):
            candidates.extend(sorted(folder.glob("sample_holdings*.csv")))
        if not candidates:
            raise loader_error

        frame = pd.read_csv(candidates[0], dtype=str)
        frame.columns = [str(c).strip() for c in frame.columns]
        total_rows = len(frame)

        for column in (WEIGHT_COLUMN, "expense_ratio"):
            if column in frame.columns:
                cleaned = (
                    frame[column].astype(str)
                    .str.replace("%", "", regex=False)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                )
                frame[column] = pd.to_numeric(cleaned, errors="coerce")

        # Drop rows whose weight is not a number (stray headers, blanks, notes)
        frame = frame.dropna(subset=[WEIGHT_COLUMN]).copy()
        for column in ("fund", "stock", "sector"):
            if column in frame.columns:
                frame[column] = frame[column].astype(str).str.strip()

        # Weights written as percentages (sum ~100) -> fractions (sum ~1)
        fund_totals = frame.groupby("fund")[WEIGHT_COLUMN].transform("sum")
        is_percent = fund_totals > 1.5
        frame.loc[is_percent, WEIGHT_COLUMN] = frame.loc[is_percent, WEIGHT_COLUMN] / 100.0

        notice = (
            f"data_loader.load_holdings() failed ({loader_error}). "
            f"Loaded {candidates[0].name} directly instead and ignored "
            f"{total_rows - len(frame)} row(s) with non-numeric weights."
        )
        return frame.reset_index(drop=True), notice


try:
    sample_holdings, loader_notice = load_sample_holdings_safely()
except Exception as error:
    st.error(f"Could not load holdings data: {error}")
    st.stop()

if loader_notice:
    st.warning(loader_notice)

# Real scheme holdings (optional): one row per stock per scheme
try:
    library = (
        pd.read_csv(LIBRARY_PATH) if LIBRARY_PATH.exists() else pd.DataFrame()
    )
except Exception as error:
    st.error(f"Could not read {LIBRARY_PATH.name}: {error}")
    st.stop()

if not library.empty:
    for numeric_column in (WEIGHT_COLUMN, "expense_ratio"):
        if numeric_column in library.columns:
            library[numeric_column] = pd.to_numeric(
                library[numeric_column], errors="coerce"
            )

library_fund_names = (
    sorted(library["fund"].unique()) if not library.empty else []
)
library_as_of = {}
if not library.empty and "as_of" in library.columns:
    library_as_of = (
        library.dropna(subset=["as_of"]).groupby("fund")["as_of"].first().to_dict()
    )

holdings = (
    pd.concat([sample_holdings, library], ignore_index=True)
    if not library.empty
    else sample_holdings
)

required_columns = {"fund", "stock", "sector", WEIGHT_COLUMN, "expense_ratio"}
missing_columns = required_columns - set(holdings.columns)
if missing_columns:
    st.error(f"Holdings dataset is missing columns: {', '.join(sorted(missing_columns))}")
    st.stop()

fund_names = sorted(holdings["fund"].unique())

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.markdown(
    """
    <div class="topbar">
        <div>
            <span class="brand">Portfolio <span>X-Ray</span></span>
            <span class="badge">MVP · Demo Data</span>
        </div>
        <div class="tagline">
            Underlying stock exposure, fund overlap<br>
            and sector concentration.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Explore how your investments overlap beneath the surface. "
    "Stock holdings, industries and weights come from official AMC portfolio "
    "disclosures stored in the holdings library."
)

# ------------------------------------------------------------------
# PDF upload: read schemes + values, then map them to holdings data
# ------------------------------------------------------------------
st.subheader("Statement PDF")
st.caption(
    "Upload a text-based CAS-style PDF. Schemes and market values are read "
    "automatically, and each scheme's stocks are looked up in the holdings library."
)

uploaded_pdf = st.file_uploader(
    "Upload a text-based PDF statement",
    type=["pdf"],
    key="statement_pdf",
)

for state_key, state_default in (
    ("pdf_text", ""),
    ("pdf_schemes", []),
    ("pdf_file_sig", ""),
):
    if state_key not in st.session_state:
        st.session_state[state_key] = state_default

if uploaded_pdf is None:
    # File removed: clear everything that came from it
    if st.session_state["pdf_file_sig"] or st.session_state["pdf_schemes"]:
        reset_pdf_state()
else:
    file_signature = f"{uploaded_pdf.name}:{uploaded_pdf.size}"

    # Process automatically whenever a new file arrives
    if file_signature != st.session_state["pdf_file_sig"]:
        reset_pdf_state()
        try:
            extracted_text = extract_pdf_text(uploaded_pdf.getvalue())
            parsed_schemes = parse_cas_schemes(extracted_text)

            for scheme in parsed_schemes:
                suggested, method = match_scheme_to_fund(
                    scheme["scheme"], library_fund_names
                )
                scheme["suggested_fund"] = suggested
                scheme["match_method"] = method

            st.session_state["pdf_text"] = extracted_text
            st.session_state["pdf_schemes"] = parsed_schemes
            st.session_state["pdf_file_sig"] = file_signature

            # Switch to the statement source if anything matched
            if any(s["suggested_fund"] for s in parsed_schemes):
                st.session_state["investment_source"] = "Statement PDF"

        except ValueError as error:
            st.error(str(error))

if st.session_state["pdf_text"]:
    with st.expander("Preview extracted PDF text"):
        st.text_area(
            "Extracted text",
            value=st.session_state["pdf_text"],
            height=220,
            disabled=True,
            key="pdf_text_preview",
        )

pdf_schemes = st.session_state["pdf_schemes"]
pdf_investments = {}

if library_fund_names:
    latest_disclosure = max(library_as_of.values(), default="")
    st.caption(
        f"Holdings library: {len(library_fund_names)} scheme(s)"
        + (f", latest disclosure {latest_disclosure}." if latest_disclosure else ".")
    )
else:
    st.warning(
        "No holdings library found. Create holdings_library.csv by running "
        "build_holdings.py on AMC portfolio disclosure files."
    )

if pdf_schemes:
    st.markdown("**Schemes found in your statement**")

    schemes_without_holdings = []

    for index, scheme in enumerate(pdf_schemes):
        info_col, status_col, amount_col = st.columns([3, 3, 2])
        matched_fund = scheme["suggested_fund"]

        with info_col:
            st.markdown(f"**{scheme['scheme']}**")
            st.caption(f"{scheme['amc']} · Folio {scheme['folio']}")

        with status_col:
            if matched_fund:
                disclosure = library_as_of.get(matched_fund, "")
                st.markdown("✅ Holdings found")
                st.caption(
                    matched_fund
                    + (f" · disclosure {disclosure}" if disclosure else "")
                )
            else:
                st.markdown("⚠️ Holdings not in library yet")
                st.caption("Add it with build_holdings.py")

        with amount_col:
            if matched_fund:
                amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.0,
                    value=float(scheme["market_value"] or 0.0),
                    step=1000.0,
                    key=f"pdf_amt_{index}",
                )
                pdf_investments[matched_fund] = (
                    pdf_investments.get(matched_fund, 0.0) + float(amount)
                )
            else:
                st.markdown(f"₹{float(scheme['market_value'] or 0):,.0f}")
                st.caption("Not analysed")
                schemes_without_holdings.append(scheme["scheme"])

    st.caption(
        "Amounts default to the market value printed in the statement; edit if needed."
    )

    if schemes_without_holdings:
        st.info(
            "These schemes are not in the analysis because their holdings are not "
            "in the library yet: "
            + "; ".join(schemes_without_holdings)
            + ". Download each AMC's monthly portfolio disclosure and run "
            "build_holdings.py. Renamed schemes may need an entry in "
            "SCHEME_ALIASES in parser.py."
        )
elif st.session_state["pdf_text"]:
    st.warning(
        "Text was extracted, but no schemes could be recognized. "
        "This parser reads statements with 'Scheme:' lines and 'Market Value' figures; "
        "other layouts may need a small tweak."
    )

# ------------------------------------------------------------------
# Sidebar: select the source for the analysis
# ------------------------------------------------------------------
st.sidebar.header("Your Portfolio")
st.sidebar.markdown(
    '<div class="side-label">Investment Source</div>',
    unsafe_allow_html=True,
)
investment_source = st.sidebar.radio(
    "Choose how to enter investments",
    ["Manual Entry", "Statement PDF"],
    key="investment_source",
)

if investment_source == "Manual Entry":
    st.sidebar.caption("Enter a hypothetical amount for each fund.")
    investments = {}
    for fund in fund_names:
        investments[fund] = st.sidebar.number_input(
            f"{fund} (₹)",
            min_value=0,
            value=10000,
            step=1000,
            key=f"manual_investment_{fund}",
        )
else:
    investments = {
        fund: amount for fund, amount in pdf_investments.items() if amount > 0
    }
    if not investments:
        st.sidebar.warning(
            "Upload a statement PDF that contains at least one scheme from the holdings library."
        )
    else:
        st.sidebar.caption("Using the amounts from the statement section.")

st.sidebar.markdown(
    '<div class="side-label">Alert Settings</div>',
    unsafe_allow_html=True,
)
stock_threshold = st.sidebar.slider(
    "Single-stock alert threshold (%)",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
)
sector_threshold = st.sidebar.slider(
    "Sector alert threshold (%)",
    min_value=20,
    max_value=80,
    value=40,
    step=5,
)

total_investment = sum(investments.values())
if total_investment <= 0:
    st.warning(
        "Enter a positive investment in at least one fund. "
        "In Statement PDF mode, upload a statement that contains at least one "
        "scheme from the holdings library."
    )
    st.stop()

# ------------------------------------------------------------------
# Run analysis once using the selected investment source
# ------------------------------------------------------------------
try:
    stock_data = calculate_stock_exposure(holdings, investments)
    investment_overlap = calculate_investment_overlap(holdings, investments)
    sector_data = calculate_sector_exposure(stock_data)
    alerts = generate_concentration_alerts(
        stock_data,
        sector_data,
        stock_threshold=float(stock_threshold),
        sector_threshold=float(sector_threshold),
    )
except Exception as error:
    st.error(f"Analysis failed: {error}")
    st.stop()

# Cash/debt/other placeholders are not real stocks or sectors: no alerts for them
alerts = [
    alert for alert in alerts
    if not str(alert.get("Name", "")).startswith(OTHER_PREFIX)
    and alert.get("Name") != OTHER_SECTOR
]

# ------------------------------------------------------------------
# Summary metrics
# ------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Investment", f"₹{total_investment:,.0f}")
col2.metric("Stocks Held Across Funds", len(stock_data))
col3.metric("Funds Analyzed", sum(amount > 0 for amount in investments.values()))
col4.metric("Concentration Alerts", len(alerts))

st.write("")

tab_overview, tab_holdings, tab_overlap, tab_costs = st.tabs(
    ["Overview", "Holdings", "Fund Overlap", "Costs"]
)

# ------------------------------------------------------------------
# Tab 1: Overview
# ------------------------------------------------------------------
with tab_overview:
    st.subheader("Portfolio Composition")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        treemap = px.treemap(
            stock_data,
            path=["sector", "stock"],
            values="exposure_value",
            title="Underlying stock exposure",
            color_discrete_sequence=CHART_COLORS,
        )
        treemap.update_traces(
            marker=dict(line=dict(color=PANEL, width=2)),
            textfont=dict(family=SANS, size=14, color=BG),
            root_color=PANEL,
        )
        style_figure(treemap, height=460)
        st.plotly_chart(treemap, use_container_width=True)

    with chart_col2:
        sector_chart = px.pie(
            sector_data,
            names="sector",
            values="exposure_value",
            hole=0.55,
            title="Allocation by sector",
            color_discrete_sequence=CHART_COLORS,
        )
        sector_chart.update_traces(
            marker=dict(line=dict(color=PANEL, width=2)),
            textfont=dict(family=SANS, size=13, color=IVORY),
            textposition="outside",
        )
        style_figure(sector_chart, height=460)
        st.plotly_chart(sector_chart, use_container_width=True)

    st.subheader("Portfolio Concentration Alerts")
    st.caption("Thresholds can be adjusted in the sidebar.")
    if not alerts:
        st.success("No stocks or sectors exceeded your selected thresholds.")
    else:
        st.write(f"Found {len(alerts)} concentration alert(s).")
        for alert in alerts:
            st.warning(
                f"**{alert['Type']}: {alert['Name']}** — "
                f"{alert['Portfolio Weight (%)']:.2f}% of the portfolio "
                f"(₹{alert['Exposure (₹)']:,.0f}). {alert['Message']}"
            )
        st.download_button(
            "Download concentration alerts (CSV)",
            data=pd.DataFrame(alerts).to_csv(index=False),
            file_name="concentration_alerts.csv",
            mime="text/csv",
        )

# ------------------------------------------------------------------
# Tab 2: Holdings
# ------------------------------------------------------------------
with tab_holdings:
    st.subheader("Underlying Stock Exposure")
    st.caption(
        "Estimated rupee exposure is calculated from each fund's holdings weights "
        "and the investment amount entered above."
    )

    display_stock_data = stock_data.copy()
    display_stock_data["Exposure (₹)"] = display_stock_data["exposure_value"].map(
        lambda value: f"₹{value:,.0f}"
    )
    display_stock_data["Portfolio Weight (%)"] = display_stock_data["portfolio_weight"].map(
        lambda value: f"{value:.2f}%"
    )
    st.dataframe(
        display_stock_data[
            ["stock", "sector", "Exposure (₹)", "Portfolio Weight (%)"]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download stock exposure (CSV)",
        data=stock_data.to_csv(index=False),
        file_name="stock_exposure.csv",
        mime="text/csv",
    )

# ------------------------------------------------------------------
# Tab 3: Fund overlap
# ------------------------------------------------------------------
with tab_overlap:
    st.subheader("Investment-Weighted Fund Overlap")
    st.caption(
        "Each cell shows the rupee amount that is exposed to the same stocks "
        "through both funds. This is allocation overlap, not a measure of risk."
    )

    if investment_overlap.empty:
        st.info("No funds with positive investments to compare.")
    else:
        heatmap = px.imshow(
            investment_overlap,
            text_auto=",.0f",
            aspect="auto",
            color_continuous_scale=[
                [0.0, "#2B352F"],
                [0.5, "#6F8A6B"],
                [1.0, "#D4B96A"],
            ],
            labels={"x": "Fund", "y": "Fund", "color": "Shared exposure (₹)"},
        )
        heatmap.update_traces(xgap=3, ygap=3)
        heatmap.update_layout(
            coloraxis_colorbar=dict(
                outlinewidth=0,
                thickness=14,
                tickfont=dict(family=SANS, color=IVORY),
                title=dict(font=dict(family=SANS, color=IVORY)),
            )
        )
        style_figure(heatmap)
        st.plotly_chart(heatmap, use_container_width=True)

    st.subheader("Compare Two Funds")
    if len(fund_names) < 2:
        st.info("At least two funds are needed for a comparison.")
    else:
        compare_col1, compare_col2 = st.columns(2)
        with compare_col1:
            fund_a = st.selectbox(
                "First fund",
                fund_names,
                key="overlap_fund_a",
            )
        other_funds = [fund for fund in fund_names if fund != fund_a]
        with compare_col2:
            default_b_index = 0
            fund_b = st.selectbox(
                "Second fund",
                other_funds,
                index=default_b_index,
                key="overlap_fund_b",
            )

        try:
            overlap_details, total_overlap = calculate_overlap_details(
                holdings, fund_a, fund_b
            )
            st.metric("Shared Stock Allocation", f"{total_overlap:.2f}%")
            st.caption(
                "For each stock, the shared allocation is the smaller of its "
                "weight in the two selected funds."
            )
            st.dataframe(
                overlap_details.style.format(
                    {
                        f"{fund_a} Weight (%)": "{:.2f}%",
                        f"{fund_b} Weight (%)": "{:.2f}%",
                        "Shared Allocation (%)": "{:.2f}%",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "Download pairwise overlap report (CSV)",
                data=overlap_details.to_csv(index=False),
                file_name="fund_overlap_report.csv",
                mime="text/csv",
            )
        except ValueError as error:
            st.error(str(error))

# ------------------------------------------------------------------
# Tab 4: Costs
# ------------------------------------------------------------------
with tab_costs:
    st.subheader("Estimated Annual Fund Expenses")
    st.caption(
        "Illustrative estimate = entered investment × expense ratio. "
        "Actual costs can vary and this does not model changing investment values."
    )

    expense_by_fund = (
        holdings[["fund", "expense_ratio"]]
        .drop_duplicates("fund")
        .set_index("fund")["expense_ratio"]
    )
    expense_rows = []
    for fund, amount in investments.items():
        ratio = float(expense_by_fund.loc[fund])
        expense_rows.append(
            {
                "Fund": fund,
                "Investment (₹)": amount,
                "Expense Ratio (%)": ratio,
                "Estimated Annual Cost (₹)": amount * ratio / 100,
            }
        )

    expense_data = pd.DataFrame(expense_rows)
    st.dataframe(
        expense_data.style.format(
            {
                "Investment (₹)": "₹{:,.0f}",
                "Expense Ratio (%)": "{:.2f}%",
                "Estimated Annual Cost (₹)": "₹{:,.2f}",
            },
            na_rep="N/A",
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download expense estimate (CSV)",
        data=expense_data.to_csv(index=False),
        file_name="estimated_fund_expenses.csv",
        mime="text/csv",
    )

# ------------------------------------------------------------------
# Footer
# ------------------------------------------------------------------
st.markdown(
    """
    <div class="colophon">
        Scheme names and values are read from the uploaded statement; stock holdings
        come from AMC portfolio disclosures in the holdings library (and a synthetic
        sample dataset for manual mode).
        Expense estimates are approximate. This tool is educational, not personalized
        financial advice.
    </div>
    """,
    unsafe_allow_html=True,
)