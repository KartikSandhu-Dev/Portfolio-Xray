"""
Build / update holdings_library.csv from official AMC portfolio disclosures.

Every AMC must publish a monthly portfolio statement (Excel) in a SEBI-
prescribed layout: name of instrument, ISIN, industry/rating, quantity,
market value, % to net assets. This script reads those files.

Usage:
    python build_holdings.py disclosure1.xlsx disclosure2.xlsx
    python build_holdings.py ppfas.xlsx --expense-ratio 0.69 --as-of 2026-09-30
    python build_holdings.py one_scheme.xlsx --scheme-name "HDFC Top 100 Fund"

Output columns (weights are fractions, each fund sums to 1.0):
    fund, stock, sector, weight, expense_ratio, isin, as_of, source

Equity lines are kept individually. Everything else (debt, cash, repo,
derivatives, unlisted) is combined into ONE row per fund named
"Other holdings (non-equity) - <fund>", so each fund sums to 100% and
two funds never appear to overlap through "Other".
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

OTHER_PREFIX = "Other holdings (non-equity)"
OTHER_SECTOR = "Other / Cash & Debt"

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
INDIAN_EQUITY_ISIN_RE = re.compile(r"^INE[0-9A-Z]{4}01[0-9A-Z]{3}$")
DATE_RE = re.compile(
    r"(\d{1,2})[-/ ]([A-Za-z]{3,9}|\d{1,2})[-/ ,]+(\d{4})"
)
DATE_MONTH_FIRST_RE = re.compile(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})")

COLUMNS = [
    "fund", "stock", "sector", "weight",
    "expense_ratio", "isin", "as_of", "source",
]


def _text(value):
    return "" if pd.isna(value) else str(value).strip()


def _to_number(value):
    """Number from a cell; understands text like '8.06%' (-> 0.0806) and '1,234.5'."""
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if text.endswith("%"):
            number = pd.to_numeric(text[:-1], errors="coerce")
            return number / 100.0 if pd.notna(number) else number
        return pd.to_numeric(text, errors="coerce")
    return pd.to_numeric(value, errors="coerce")


def find_header_row(raw):
    """Row index that holds the column titles (has 'ISIN' and a % column)."""
    for index in range(min(len(raw), 40)):
        cells = [_text(v).lower() for v in raw.iloc[index].tolist()]
        has_isin = any("isin" in c for c in cells)
        has_pct = any(
            "%" in c and ("net" in c or "nav" in c or "asset" in c or "aum" in c)
            for c in cells
        ) or any(c.startswith("% to") for c in cells)
        if has_isin and has_pct:
            return index
    return None


def map_columns(header_cells):
    """Return column positions for name, isin, sector, weight."""
    lowered = [_text(c).lower() for c in header_cells]
    positions = {"name": None, "isin": None, "sector": None, "weight": None}

    for pos, cell in enumerate(lowered):
        if positions["isin"] is None and "isin" in cell:
            positions["isin"] = pos
        elif positions["name"] is None and (
            "name of the instrument" in cell
            or "instrument" in cell
            or "security" in cell
            or "company" in cell
        ):
            positions["name"] = pos
        elif positions["sector"] is None and (
            "industry" in cell or "rating" in cell or "sector" in cell
        ):
            positions["sector"] = pos
        elif positions["weight"] is None and "%" in cell:
            positions["weight"] = pos

    if positions["name"] is None and positions["isin"] not in (None, 0):
        positions["name"] = positions["isin"] - 1

    return positions


def find_scheme_name(raw, header_index, sheet_name):
    """Scheme name from the lines above the table, else the sheet name."""
    def clean(text):
        text = re.sub(r"\s*\((?:an?)\b.*$", "", text, flags=re.I)
        return re.sub(r"\s+", " ", text).strip()

    # Best case: an explicit "SCHEME NAME : <name>" line
    for index in range(min(header_index, 10)):
        for cell in raw.iloc[index].tolist():
            match = re.search(r"scheme\s*name\s*:?\s*(.+)", _text(cell), re.I)
            if match and len(match.group(1).strip()) > 3:
                return clean(match.group(1))

    for index in range(min(header_index, 10)):
        for cell in raw.iloc[index].tolist():
            text = _text(cell)
            lowered = text.lower()
            if len(text) < 6 or "portfolio statement" in lowered:
                continue
            if "back to index" in lowered:
                continue
            if lowered.startswith(("as on", "as at", "monthly")):
                continue
            if any(k in lowered for k in ("fund", "scheme", "etf", "plan")):
                text = re.sub(r"\s*\((?:an?)\b.*$", "", text, flags=re.I)
                return re.sub(r"\s+", " ", text).strip()
    return sheet_name


def find_as_of(raw, header_index):
    months = {
        m: i for i, m in enumerate(
            ["jan", "feb", "mar", "apr", "may", "jun",
             "jul", "aug", "sep", "oct", "nov", "dec"], start=1)
    }
    for index in range(min(header_index, 12)):
        for cell in raw.iloc[index].tolist():
            text = _text(cell)
            match = DATE_RE.search(text)
            if match:
                day, month, year = match.groups()
            else:
                match = DATE_MONTH_FIRST_RE.search(text)
                if not match:
                    continue
                month, day, year = match.groups()
            if month.isdigit():
                month_number = int(month)
            else:
                month_number = months.get(month[:3].lower())
            if month_number:
                return f"{int(year):04d}-{month_number:02d}-{int(day):02d}"
    return ""


def parse_sheet(raw, sheet_name, scheme_override=None, as_of_override=None):
    """Return (fund_name, rows DataFrame) or None when the sheet has no table."""
    header_index = find_header_row(raw)
    if header_index is None:
        return None

    pos = map_columns(raw.iloc[header_index].tolist())
    if pos["isin"] is None or pos["weight"] is None or pos["name"] is None:
        return None

    fund = scheme_override or find_scheme_name(raw, header_index, sheet_name)
    as_of = as_of_override or find_as_of(raw, header_index)

    records = []
    for index in range(header_index + 1, len(raw)):
        row = raw.iloc[index]
        weight = _to_number(row.iloc[pos["weight"]])
        if pd.isna(weight):
            continue
        records.append(
            {
                "name": _text(row.iloc[pos["name"]]),
                "isin": _text(row.iloc[pos["isin"]]).upper(),
                "sector": (
                    _text(row.iloc[pos["sector"]])
                    if pos["sector"] is not None else ""
                ),
                "weight": float(weight),
            }
        )

    table = pd.DataFrame(records)
    if table.empty:
        return None

    # Weights may be written as fractions (0.0775) or percentages (7.75)
    valid = table[table["isin"].map(lambda s: bool(ISIN_RE.match(s)))]
    if valid["weight"].sum() > 1.5:
        table["weight"] = table["weight"] / 100.0

    return fund, table, as_of


def split_equity(table):
    """Equity rows (listed Indian + foreign equity ISINs) vs everything else."""
    def is_equity(isin):
        if INDIAN_EQUITY_ISIN_RE.match(isin):
            return True
        # Overseas equity: valid ISIN that is not an Indian security
        return bool(ISIN_RE.match(isin)) and not isin.startswith("IN")

    mask = table["isin"].map(is_equity)
    return table[mask].copy(), table[~mask].copy()


def build_rows(fund, table, as_of, expense_ratio, source):
    equity, _ = split_equity(table)

    equity["sector"] = equity["sector"].replace("", "Unclassified")
    grouped = (
        equity.groupby("isin", as_index=False)
        .agg(stock=("name", "first"), sector=("sector", "first"),
             weight=("weight", "sum"))
    )

    total = grouped["weight"].sum()
    if total > 1.0:
        grouped["weight"] = grouped["weight"] / total
        total = 1.0

    rows = grouped.assign(
        fund=fund,
        expense_ratio=expense_ratio,
        as_of=as_of,
        source=source,
    )

    remainder = round(1.0 - total, 10)
    if remainder > 1e-9:
        other = pd.DataFrame(
            [
                {
                    "fund": fund,
                    "stock": f"{OTHER_PREFIX} - {fund}",
                    "sector": OTHER_SECTOR,
                    "weight": remainder,
                    "expense_ratio": expense_ratio,
                    "isin": "",
                    "as_of": as_of,
                    "source": source,
                }
            ]
        )
        rows = pd.concat([rows, other], ignore_index=True)

    return rows[COLUMNS].sort_values("weight", ascending=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("files", nargs="+", help="AMC disclosure .xlsx/.xls files")
    parser.add_argument("--out", default="holdings_library.csv")
    parser.add_argument("--expense-ratio", type=float, default=None,
                        help="Expense ratio in %% (applies to all schemes in this run)")
    parser.add_argument("--scheme-name", default=None,
                        help="Override scheme name (single-scheme files)")
    parser.add_argument("--as-of", default=None, help="Disclosure date YYYY-MM-DD")
    args = parser.parse_args()

    out_path = Path(args.out)
    library = (
        pd.read_csv(out_path) if out_path.exists()
        else pd.DataFrame(columns=COLUMNS)
    )

    added = []
    for file_name in args.files:
        path = Path(file_name)
        sheets = pd.read_excel(path, sheet_name=None, header=None)

        for sheet_name, raw in sheets.items():
            parsed = parse_sheet(raw, sheet_name, args.scheme_name, args.as_of)
            if parsed is None:
                continue

            fund, table, as_of = parsed
            rows = build_rows(
                fund, table, as_of,
                expense_ratio=(
                    args.expense_ratio if args.expense_ratio is not None
                    else float("nan")
                ),
                source=path.name,
            )
            library = library[library["fund"] != fund]
            library = pd.concat([library, rows], ignore_index=True)
            added.append((fund, len(rows), as_of))

    if not added:
        sys.exit("No portfolio tables found. Check that the file has ISIN and % to Net Assets columns.")

    library.to_csv(out_path, index=False)
    for fund, count, as_of in added:
        print(f"Added {fund}: {count} rows (as of {as_of or 'unknown'})")
    print(f"Saved {out_path} with {library['fund'].nunique()} scheme(s).")


if __name__ == "__main__":
    main()