# Portfolio X-Ray

**A mutual-fund portfolio overlap and exposure analyzer built as a hackathon prototype.**

Portfolio X-Ray helps users look through a collection of mutual funds and understand how their underlying stock and sector exposures may overlap. I vibe-coded this project for a hackathon to turn the idea into a working, interactive prototype and explore how portfolio-analysis tools can make overlapping holdings easier to understand.

> **Project status:** Hackathon MVP / prototype. The included holdings are synthetic demo data, not real or current mutual-fund disclosures. The PDF workflow currently extracts selectable text and looks for supported sample fund names; it does not automatically parse real Indian Consolidated Account Statements (CAS) or reliably extract investment amounts.

## Features

- **Stock-level exposure:** Estimate how much of the entered portfolio is exposed to each stock through the selected funds.
- **Sector composition:** View estimated sector exposure with interactive charts.
- **Fund overlap:** Compare funds by their shared stock allocations and visualize rupee-denominated overlap based on the amounts entered.
- **Concentration alerts:** Flag stock or sector exposures that cross user-configurable thresholds.
- **Estimated annual fund expenses:** Estimate costs from the sample expense ratios and entered investment amounts.
- **PDF text extraction:** Upload a text-based PDF statement and inspect its extracted text.
- **Fund-name matching:** Search the extracted text for fund names that exist in the demo dataset.
- **CSV exports:** Download supported analysis results for further inspection.
- **Interactive dashboard:** Built with Streamlit and Plotly.

## Tech stack

- **Python**
- **Streamlit** — interactive web dashboard
- **pandas** — tabular data and calculations
- **Plotly** — interactive charts
- **PyMuPDF** (`pymupdf`) — PDF text extraction

## Project structure

```text
Portfolio-Xray/
├── main.py                  # Streamlit dashboard and UI
├── analysis.py              # Portfolio exposure, overlap, and alert calculations
├── data_loader.py           # Loads and validates holdings data
├── parser.py                # PDF text extraction and sample fund-name matching
├── requirements.txt         # Python dependencies
├── data/
│   └── sample_holdings.csv  # Synthetic demonstration holdings
├── .gitignore
└── README.md
```

## Getting started

### Requirements

- Python 3.10 or newer is recommended.
- Git (only needed to publish or clone the repository).

### 1. Clone the repository

Replace `YOUR-GITHUB-USERNAME` with your GitHub username after creating the repository.

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/Portfolio-Xray.git
cd Portfolio-Xray
```

If you are uploading an existing local project for the first time, you can skip cloning and open a terminal in your project folder.

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python directly or follow the execution-policy guidance in the official PowerShell documentation. Avoid changing system-wide security settings just to run this project.

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

### 4. Run the dashboard

```bash
streamlit run main.py
```

Streamlit will print a local URL, usually `http://localhost:8501`. Open it in your browser.

## Using the app

1. Choose **Manual Entry** or **PDF-confirmed Funds** in the sidebar.
2. In Manual Entry mode, enter hypothetical investment amounts for the available demo funds.
3. In PDF mode, upload a text-based PDF and extract its text.
4. Review any recognized demo fund names and enter/confirm the amounts manually.
5. Explore the **Overview**, **Holdings**, **Fund Overlap**, and **Costs** sections.
6. Adjust concentration thresholds and download available CSV reports.

A scanned PDF may not contain selectable text and may require OCR. The current prototype does not include OCR.

## How the analysis works

### Stock exposure

For each selected fund, the app multiplies the amount invested by each stock's portfolio weight. It then adds the resulting exposure to the same stock across the selected funds.

For example, if ₹10,000 is invested in a fund whose demo holdings assign 40% to a stock, the estimated exposure through that fund is ₹4,000.

### Portfolio weight

The estimated exposure to each stock is divided by the total amount invested in the analyzed funds to calculate its percentage of the analyzed portfolio.

### Fund overlap

For two funds, the prototype compares the weights assigned to each stock and sums the smaller weight for every stock shared by the funds. This provides a simple allocation-overlap measure when each fund's holdings are complete and normalized to 100%.

The dashboard's rupee overlap view applies the same minimum-exposure idea to the amounts invested in each fund. This is an exposure comparison, not a measure of identical risk, performance, or future returns.

### Concentration alerts

The app flags individual stocks or sectors whose calculated portfolio weights meet or exceed the thresholds selected in the sidebar. These are user-configurable demo thresholds, not universal investment recommendations.

### Estimated annual expenses

The prototype estimates annual expenses by multiplying the entered investment amount by the sample expense ratio. Actual costs can differ as investment values change, and this estimate does not account for every possible charge.

## Data and limitations

- The supplied `data/sample_holdings.csv` dataset is synthetic and intended for demonstrating the calculations and interface.
- The example fund names are placeholders, not verified real schemes.
- The app's fund-name matcher only recognizes names found in the loaded demo dataset.
- PDF text extraction is not the same as CAS parsing. Investment values are entered manually; the prototype does not claim to extract them accurately from a real statement.
- Holdings data must be complete and internally consistent for the overlap calculations to be meaningful.
- Expense estimates are approximate.
- This project is a learning/hackathon prototype, not a production-grade financial product.

## Roadmap

- [ ] Add tests for stock exposure, overlap, and expense calculations.
- [ ] Improve validation and reporting for incomplete holdings.
- [ ] Support a clearly defined, anonymized CAS format with test fixtures.
- [ ] Parse scheme names and investment values with explicit user review and confirmation.
- [ ] Add OCR support for scanned statements, if needed.
- [ ] Add data-source attribution, timestamps, and update handling for real holdings data.
- [ ] Improve deployment and automated checks.

## Running tests

Automated tests have not yet been included in this prototype. Before relying on changes, manually test the calculations using small, known datasets and verify the results.

## Why I built it

I vibe-coded Portfolio X-Ray for a hackathon: the goal was to move quickly from an idea to a tangible prototype, experiment with the data flow and visual design, and explore how a portfolio X-ray could reveal overlapping stock exposure across multiple funds. The project is a starting point, and the next step is to validate the calculations and build a reliable pipeline for real data.

## Disclaimer

This project is for educational and demonstration purposes only. It does not provide personalized financial advice, recommend any investment, or guarantee the accuracy of results. Do not upload sensitive financial statements to an untrusted deployment. Use synthetic or appropriately anonymized documents when testing.

## License

No license has been added yet. If you want others to reuse, modify, or distribute this project, choose and add a license file before presenting the repository as open source.
