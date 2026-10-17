# Portfolio X-Ray

**A mutual-fund portfolio overlap and exposure analyzer built as a hackathon prototype.**

Portfolio X-Ray helps users look through a collection of mutual funds and understand how their underlying stock and sector exposures may overlap. Upload a Consolidated Account Statement (CAS) style PDF, and the app detects your schemes and market values, looks up each scheme's real stock holdings from a holdings library built from official AMC portfolio disclosures, and shows where your money is really concentrated. I vibe-coded this project for a hackathon to turn the idea into a working, interactive prototype.

> **Project status:** Hackathon MVP / prototype. The bundled `data/sample_holdings.csv` is synthetic demo data (made-up weights, expense ratios and fund names). Real scheme holdings only appear for schemes you import into `holdings_library.csv` with `build_holdings.py`. The statement parser has been tested on a sample CAS-style PDF only; real CAMS/KFintech statements may need small adjustments.

## Live demo

**Deployed app:** [APP LINK](https://portfolio-xray-ks.streamlit.app/)

See [Deployment](#deployment-streamlit-community-cloud) for how it was published.

## Features

- **Statement PDF upload:** Reads scheme names, AMC, folio and market values from a text-based CAS-style PDF.
- **Automatic scheme detection:** Matches each detected scheme to its holdings in the library (exact, partial or fuzzy name match, plus optional aliases for renamed schemes). No manual mapping.
- **Holdings library from official data:** `build_holdings.py` converts AMC monthly portfolio disclosure Excel files into `holdings_library.csv` (stock, industry, weight, disclosure date, source file).
- **Stock-level exposure:** Estimates how much of the portfolio is exposed to each stock through the selected funds.
- **Sector composition:** Treemap and donut charts of estimated exposure.
- **Fund overlap:** Rupee-denominated overlap heatmap, plus a pairwise "Compare Two Funds" breakdown.
- **Concentration alerts:** Flags stocks or sectors above user-configurable thresholds. Cash/debt/"other" placeholders are never flagged.
- **Estimated annual fund expenses:** Investment × expense ratio (shows N/A when a library fund has no expense ratio).
- **CSV exports:** Download alerts, stock exposure, pairwise overlap and expense estimates.
- **Manual mode:** Enter hypothetical amounts for any fund in the dataset or library.
- **Interactive dashboard:** Streamlit and Plotly, with a dark, old-money inspired theme.

## Tech stack

- **Python** (3.10 or newer)
- **Streamlit**: dashboard
- **pandas**: data processing
- **Plotly**: interactive charts
- **PyMuPDF** (`pymupdf`): PDF text extraction
- **openpyxl** (and `xlrd` for old `.xls` files): only needed locally, to run `build_holdings.py`

## Project structure

```text
Portfolio-Xray/
├── main.py                  # Streamlit dashboard and UI
├── analysis.py              # Exposure, overlap and alert calculations
├── data_loader.py           # Loads, cleans and validates sample_holdings.csv
├── parser.py                # PDF text extraction, CAS scheme parsing, scheme-to-fund matching
├── build_holdings.py        # Imports AMC disclosure Excel files into holdings_library.csv
├── holdings_library.csv     # Generated: real scheme holdings (commit it so the deployed app can use it)
├── requirements.txt         # Python dependencies
├── data/
│   └── sample_holdings.csv  # Synthetic demonstration holdings
├── .streamlit/
│   └── config.toml          # Theme
├── .gitignore
├── LICENSE
└── README.md
```

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/KartikSandhu-Dev/Portfolio-Xray.git
cd Portfolio-Xray
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

To use the holdings importer, also run `pip install openpyxl` (and `pip install xlrd` if an AMC file is the old `.xls` format).

### 4. Run the dashboard

```bash
streamlit run main.py
```

Streamlit prints a local URL, usually `http://localhost:8501`.

## Using the app

1. Upload a text-based CAS-style PDF under **Statement PDF**. Schemes and market values are read automatically.
2. Each scheme shows **✅ Holdings found** (with the disclosure date) or **⚠️ Holdings not in library yet**. Only schemes with holdings are analysed.
3. Edit any amount if needed. Amounts default to the market value printed in the statement.
4. Or switch the sidebar to **Manual Entry** and type hypothetical amounts per fund.
5. Explore **Overview**, **Holdings**, **Fund Overlap** and **Costs**.
6. Adjust the alert thresholds in the sidebar and download CSV reports.

A scanned PDF may not contain selectable text and would need OCR, which is not included.

## Building the holdings library

A CAS only says which schemes you own and what they are worth. It never lists the stocks inside a fund. Those come from the monthly portfolio disclosure each AMC must publish (an Excel file with instrument, ISIN, industry and % of net assets).

1. Download the latest monthly portfolio disclosure for each scheme from its AMC's website (usually under Downloads or Statutory Disclosures).
2. Put the files in the project folder and run:

   ```bash
   python build_holdings.py hdfc.xlsx ppfas.xlsx sbi.xlsx
   ```

   Optional flags:

   ```bash
   python build_holdings.py file.xlsx --expense-ratio 0.69 --as-of 2026-09-30
   python build_holdings.py file.xlsx --scheme-name "HDFC Top 100 Fund"
   ```

3. This creates or updates `holdings_library.csv` next to `main.py`. Re-importing a scheme replaces its old rows.
4. Restart the app and upload your statement again.

What the importer does:

- Finds the table by its `ISIN` and `% to Net Assets / AUM` columns and reads each sheet as one scheme.
- Keeps listed equity lines individually, using the industry given in the disclosure.
- Combines debt, cash, repo, derivatives and unlisted holdings into **one** row per fund, named `Other holdings (non-equity) - <fund>`, so each fund adds up to 100% and two funds never appear to overlap through "Other".
- Stores weights as fractions (0.0825 = 8.25%) with the disclosure date and source file.

If a scheme will not match, it may have been renamed. Add an entry to `SCHEME_ALIASES` in `parser.py`, mapping the normalized statement name to the fund name in the library.

## Deployment (Streamlit Community Cloud)

The app is deployed on [Streamlit Community Cloud](https://streamlit.io/cloud), which runs directly from this GitHub repository.

**Live link:** [STREAMLIT LINK](https://portfolio-xray-ks.streamlit.app/)

### Before deploying

- Push the project to GitHub (public repository, or private with access granted to Streamlit).
- Make sure `requirements.txt` includes at least: `streamlit`, `pandas`, `plotly` and `pymupdf`.
- **Commit `holdings_library.csv` and `data/sample_holdings.csv`.** The cloud app only has the files in the repository, so without the library file, uploaded statements will show "Holdings not in library yet" for every scheme.
- `build_holdings.py` runs on your machine to refresh the library; the deployed app does not need `openpyxl`.

### Deploy steps

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **Create app** (or **New app**) and choose **Deploy a public app from GitHub**.
3. Select the repository `KartikSandhu-Dev/Portfolio-Xray`, branch `main`.
4. Set **Main file path** to `main.py`.
5. Under **Advanced settings**, choose Python 3.10 or newer (the project has a file named `parser.py`, which clashes with an old standard-library module on very old Python versions).
6. Click **Deploy**. The first build takes a few minutes while dependencies install.
7. Copy the app's URL and paste it into the **Live demo** line at the top of this README.

### Updating the live app

Any push to `main` redeploys automatically:

```bash
git add .
git commit -m "describe your change"
git push
```

To add new schemes, run `build_holdings.py` locally, then commit and push the updated `holdings_library.csv`.

### Privacy note

A deployed app is reachable by anyone with the link. Do not upload real financial statements to it. Use the sample or anonymized PDFs for demos.

## How the analysis works

### Stock exposure

For each selected fund, the app multiplies the amount invested by each stock's portfolio weight, then adds the exposure to the same stock across funds. For example, ₹10,000 in a fund that holds a stock at 40% gives ₹4,000 of exposure to that stock through that fund.

### Portfolio weight

Each stock's estimated exposure is divided by the total amount invested in the analysed funds.

### Fund overlap

For two funds, the app sums the smaller of the two weights for every stock they share. The rupee heatmap applies the same minimum-exposure idea to the amounts invested. This is an allocation comparison, not a measure of identical risk, performance or future returns.

### Concentration alerts

Stocks or sectors at or above the sidebar thresholds are flagged. Thresholds are adjustable demo values, not investment recommendations. The "Other holdings" placeholder rows are excluded.

### Estimated annual expenses

Entered investment × expense ratio. Actual costs vary, and this ignores changing investment values and other charges.

## Data and limitations

- `data/sample_holdings.csv` is **synthetic**: real company names with made-up weights, expense ratios and fund names. It is for demonstrating the interface and calculations only.
- Real holdings are only as good as the disclosure files you import. Each scheme's data is a snapshot as of its disclosure date and goes stale as the fund trades.
- Schemes not in `holdings_library.csv` are listed but not analysed.
- The statement parser was built and tested against one sample CAS-style layout. Real statements from CAMS, KFintech or MFCentral may use different layouts and need parser tweaks.
- AMC disclosure files vary in layout. The importer targets the SEBI-prescribed columns, and some files may need adjustments.
- Funds that are mostly debt or hold many derivatives will show a large "Other holdings" share, because only equity lines are itemised.
- Overseas equities in a fund are included as stocks, with whatever industry label the disclosure gives.
- Investment values come from the statement's printed market value, which you can edit. Verify them against your statement.
- Expense ratios for imported schemes are blank unless you pass `--expense-ratio`.
- Scanned PDFs need OCR, which is not included.
- Holdings data must be complete and normalised to 100% per fund for the overlap calculations to work.
- This is a learning/hackathon prototype, not a production-grade financial product.

## Roadmap

- [ ] Add automated tests for exposure, overlap, expense calculations and the importer.
- [ ] Test the parser against more real, anonymized CAS layouts (CAMS, KFintech, MFCentral).
- [ ] Automate monthly refresh of the holdings library from AMC or AMFI sources.
- [ ] Add a scheme alias and rename table for renamed funds.
- [ ] Add per-scheme expense ratios and plan type (direct/regular) from official sources.
- [ ] Add OCR support for scanned statements, if needed.
- [ ] Add "what-if" rebalancing scenarios.

## Running tests

Automated tests are not yet included. Before relying on changes, check calculations manually with small, known datasets and compare the results.

## Why I built it

I vibe-coded Portfolio X-Ray for a hackathon: the goal was to move quickly from an idea to a tangible prototype, experiment with the data flow and visual design, and show how a portfolio X-ray can reveal overlapping stock exposure across funds. The next step is to validate the calculations and build a reliable pipeline for real, refreshable data.

## Disclaimer

This project is for educational and demonstration purposes only. It does not provide personalized financial advice, recommend any investment, or guarantee the accuracy of results. Do not upload sensitive financial statements to an untrusted or public deployment. Use synthetic or appropriately anonymized documents when testing.
