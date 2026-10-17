import re
from difflib import SequenceMatcher

import pymupdf


# ------------------------------------------------------------------
# 1. PDF -> text
# ------------------------------------------------------------------
def extract_pdf_text(pdf_bytes):
    """
    Extract selectable text from an uploaded PDF.

    pdf_bytes is the file content supplied by Streamlit.
    """

    try:
        with pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf",
        ) as document:

            if document.needs_pass:
                raise ValueError(
                    "This PDF is password-protected. "
                    "Use an accessible statement PDF."
                )

            pages = []

            for page_number, page in enumerate(document, start=1):
                page_text = page.get_text("text", sort=True)

                if page_text.strip():
                    pages.append(
                        f"--- Page {page_number} ---\n{page_text}"
                    )

            extracted_text = "\n\n".join(pages)

            if not extracted_text.strip():
                raise ValueError(
                    "No selectable text was found. "
                    "The PDF may be scanned and require OCR."
                )

            return extracted_text

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(
            f"Could not read this PDF: {error}"
        ) from error


# ------------------------------------------------------------------
# 2. Text -> schemes (name, AMC, folio, units, NAV, market value)
# ------------------------------------------------------------------
AMOUNT = r"([\d,]+(?:\.\d+)?)"

FOLIO_RE = re.compile(
    r"^(?P<amc>.+?)\s+Folio\s*No\s*:\s*(?P<folio>[\w/\-]+)", re.I
)
ISIN_RE = re.compile(r"ISIN\s*:\s*([A-Z]{2}[A-Z0-9]{10})", re.I)
SCHEME_RE = re.compile(r"^Scheme\s*:\s*(?P<name>.+?)\s*$", re.I)
CLOSING_RE = re.compile(r"Closing\s+Unit\s+Balance\s*:\s*" + AMOUNT, re.I)
NAV_RE = re.compile(r"NAV[^:\d]*(?:on[^:]*)?:\s*(?:INR)?\s*" + AMOUNT, re.I)
MARKET_RE = re.compile(r"Market\s+Value[^:\d]*:\s*(?:INR)?\s*" + AMOUNT, re.I)
COST_RE = re.compile(r"Cost\s+Value[^:\d]*:\s*(?:INR)?\s*" + AMOUNT, re.I)
SUMMARY_ROW_RE = re.compile(r"^(?P<name>.+?)\s+(?P<value>[\d,]+\.\d{2})$")


def parse_amount(value):
    """Convert '3,33,132.00' (Indian grouping) into 333132.0."""
    return float(str(value).replace(",", ""))


def _parse_summary_values(text):
    """Read the 'Portfolio Summary' table: scheme name -> market value."""
    values = {}
    in_summary = False

    for raw in text.splitlines():
        line = raw.strip()

        if re.search(r"Portfolio\s+Summary", line, re.I):
            in_summary = True
            continue

        if not in_summary or not line:
            continue

        if line.upper().startswith("TOTAL") or line.lower().startswith(
            "disclaimer"
        ):
            break

        row = SUMMARY_ROW_RE.match(line)
        if row:
            values[row.group("name").strip()] = parse_amount(
                row.group("value")
            )

    return values


def parse_cas_schemes(extracted_text):
    """
    Parse a CAS-style statement into a list of scheme dictionaries.

    Each dictionary has: amc, folio, scheme, isin, closing_units, nav,
    cost_value, market_value. Missing numbers are None.

    The CAS only contains what you own and what it is worth. It never
    contains stock holdings, sectors or weights; those come from the
    holdings dataset.
    """

    schemes = []
    current_amc = ""
    current_folio = ""
    current_isin = ""
    current = None

    for raw in extracted_text.splitlines():
        line = " ".join(raw.split())

        if not line or line.startswith("--- Page"):
            continue

        # AMC + folio header line
        folio_match = FOLIO_RE.match(line)
        if folio_match:
            current_amc = folio_match.group("amc").strip()
            current_folio = folio_match.group("folio").strip()
            isin_match = ISIN_RE.search(line)
            current_isin = isin_match.group(1).upper() if isin_match else ""
            current = None
            continue

        # Scheme name line starts a new scheme record
        scheme_match = SCHEME_RE.match(line)
        if scheme_match:
            name = ISIN_RE.sub("", scheme_match.group("name")).strip(" -|")
            current = {
                "amc": current_amc,
                "folio": current_folio,
                "scheme": name,
                "isin": current_isin,
                "closing_units": None,
                "nav": None,
                "cost_value": None,
                "market_value": None,
            }
            schemes.append(current)
            continue

        if current is None:
            continue

        closing = CLOSING_RE.search(line)
        if closing:
            current["closing_units"] = parse_amount(closing.group(1))

        nav = NAV_RE.search(line)
        if nav:
            current["nav"] = parse_amount(nav.group(1))

        cost = COST_RE.search(line)
        if cost:
            current["cost_value"] = parse_amount(cost.group(1))

        market = MARKET_RE.search(line)
        if market:
            current["market_value"] = parse_amount(market.group(1))

    # Fall back to the Portfolio Summary table for missing values
    summary_values = _parse_summary_values(extracted_text)

    for scheme in schemes:
        if scheme["market_value"] is None:
            scheme["market_value"] = summary_values.get(scheme["scheme"])

        # Last resort: units x NAV
        if (
            scheme["market_value"] is None
            and scheme["closing_units"] is not None
            and scheme["nav"] is not None
        ):
            scheme["market_value"] = round(
                scheme["closing_units"] * scheme["nav"], 2
            )

    # No scheme blocks at all, but a summary table exists
    if not schemes and summary_values:
        for name, value in summary_values.items():
            schemes.append(
                {
                    "amc": "",
                    "folio": "",
                    "scheme": name,
                    "isin": "",
                    "closing_units": None,
                    "nav": None,
                    "cost_value": None,
                    "market_value": value,
                }
            )

    return schemes


# ------------------------------------------------------------------
# 3. Scheme name -> fund name in the holdings dataset
# ------------------------------------------------------------------
# Words that appear in real scheme names but do not identify the fund
NOISE_WORDS = {
    "fund", "growth", "option", "plan", "direct", "regular", "idcw",
    "dividend", "payout", "reinvestment", "scheme", "mutual", "the",
    "of", "and", "a", "an", "-",
}

# Schemes get renamed (SEBI re-categorisation, AMC decisions), so the name on an
# old statement can differ from the name in the AMC's current disclosure.
# Map the normalized statement name -> the fund name used in holdings_library.csv.
# Example (verify the current name on the AMC website before using):
#   "hdfc top 100": "HDFC Large Cap Fund",
SCHEME_ALIASES = {}


def _tokens(name):
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", name.casefold())
    return [word for word in cleaned.split() if word not in NOISE_WORDS]


def _normalize(name):
    return " ".join(_tokens(name))


def match_scheme_to_fund(scheme_name, known_funds, fuzzy_cutoff=0.8):
    """
    Suggest which dataset fund a statement scheme corresponds to.

    Returns (fund_name or None, method), where method is one of
    'alias', 'exact', 'contains', 'fuzzy' or 'none'.
    """

    scheme_key = _normalize(scheme_name)

    # 1. Manual alias (compared by normalized name)
    alias = SCHEME_ALIASES.get(scheme_key)
    if alias:
        for fund in known_funds:
            if _normalize(fund) == _normalize(alias):
                return fund, "alias"

    scheme_tokens = set(_tokens(scheme_name))
    best_fund, best_score = None, 0.0

    for fund in known_funds:
        fund_key = _normalize(fund)

        # Exact raw-name match (works for funds like "Growth Fund")
        if " ".join(fund.casefold().split()) == " ".join(
            scheme_name.casefold().split()
        ):
            return fund, "exact"

        # Names made only of noise words cannot be matched safely
        if not fund_key:
            continue

        # 2. Same identifying words
        if fund_key == scheme_key:
            return fund, "exact"

        # 3. Every identifying word of the fund appears in the scheme
        if set(fund_key.split()) <= scheme_tokens:
            return fund, "contains"

        # 4. Fuzzy similarity
        score = SequenceMatcher(None, fund_key, scheme_key).ratio()
        if score > best_score:
            best_fund, best_score = fund, score

    if best_fund is not None and best_score >= fuzzy_cutoff:
        return best_fund, "fuzzy"

    return None, "none"


def find_known_funds(extracted_text, known_funds):
    """
    Kept for backwards compatibility: exact known fund names found in text.
    """

    normalized_text = " ".join(extracted_text.casefold().split())

    return [
        fund
        for fund in known_funds
        if " ".join(fund.casefold().split()) in normalized_text
    ]