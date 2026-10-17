from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).parent / "data" / "sample_holdings.csv"

REQUIRED_COLUMNS = {
    "fund",
    "stock",
    "sector",
    "weight",
    "expense_ratio",
}


def _clean_numeric(series):
    """
    Convert a column to numbers.

    Understands text such as '40%' (becomes 0.40), '1,200' and ' 0.5 '.
    Returns (numbers, bad_mask) where bad_mask marks values that were
    present but could not be read as numbers.
    """
    text = series.astype(str).str.strip()
    is_percent = text.str.endswith("%")

    cleaned = text.str.replace("%", "", regex=False).str.replace(",", "", regex=False)
    numbers = pd.to_numeric(cleaned, errors="coerce")
    numbers = numbers.where(~is_percent, numbers / 100.0)

    was_present = series.notna() & (text != "") & (text.str.lower() != "nan")
    bad_mask = was_present & numbers.isna()
    return numbers, bad_mask


def load_holdings():
    holdings = pd.read_csv(DATA_FILE, dtype=str)
    holdings.columns = [str(column).strip() for column in holdings.columns]

    missing_columns = REQUIRED_COLUMNS - set(holdings.columns)

    if missing_columns:
        raise ValueError(
            f"Missing columns: {', '.join(sorted(missing_columns))}"
        )

    if holdings.empty:
        raise ValueError("The holdings dataset is empty.")

    # Tidy text columns so the same fund is always spelled the same way
    for column in ("fund", "stock", "sector"):
        holdings[column] = holdings[column].astype(str).str.strip()

    # Drop accidentally repeated header lines inside the file
    repeated_header = (holdings["fund"].str.lower() == "fund") & (
        holdings["weight"].astype(str).str.lower().str.strip() == "weight"
    )
    holdings = holdings[~repeated_header].copy()

    # Convert the numeric columns; report exactly which rows are unreadable
    for column in ("weight", "expense_ratio"):
        numbers, bad_mask = _clean_numeric(holdings[column])

        if bad_mask.any():
            examples = [
                f"line {index + 2}: {holdings.loc[index, 'fund']} / "
                f"{holdings.loc[index, 'stock']} -> '{holdings.loc[index, column]}'"
                for index in holdings[bad_mask].index[:5]
            ]
            raise ValueError(
                f"Column '{column}' has values that are not numbers "
                f"({int(bad_mask.sum())} row(s)). First problems: "
                + "; ".join(examples)
            )

        holdings[column] = numbers

    holdings = holdings.reset_index(drop=True)

    if holdings[list(REQUIRED_COLUMNS)].isnull().any().any():
        raise ValueError("The dataset contains empty values.")

    if not holdings["weight"].between(0, 1).all():
        raise ValueError("Stock weights must be between 0 and 1.")

    if (holdings["expense_ratio"] < 0).any():
        raise ValueError("Expense ratios cannot be negative.")

    totals = holdings.groupby("fund")["weight"].sum()

    if not ((totals - 1.0).abs() < 0.000001).all():
        raise ValueError(
            "Each fund's stock weights must add up to 1.00."
        )

    return holdings