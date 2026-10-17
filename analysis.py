import pandas as pd


def calculate_stock_exposure(holdings, investments):
    """
    Calculate the amount invested indirectly in each stock.

    holdings: DataFrame containing fund holdings and stock weights.
    investments: dictionary mapping fund names to investment amounts.
    """

    if not investments:
        raise ValueError("Enter at least one fund investment.")

    if any(amount < 0 for amount in investments.values()):
        raise ValueError("Investment amounts cannot be negative.")

    total_investment = sum(investments.values())

    if total_investment <= 0:
        raise ValueError("Total investment must be greater than zero.")

    available_funds = set(holdings["fund"].unique())
    requested_funds = set(investments.keys())

    unknown_funds = requested_funds - available_funds

    if unknown_funds:
        raise ValueError(
            f"No holdings data for: {', '.join(sorted(unknown_funds))}"
        )

    # Keep only funds included in the investment dictionary.
    data = holdings[holdings["fund"].isin(requested_funds)].copy()

    # Attach each fund's investment amount to its holdings.
    data["investment"] = data["fund"].map(investments)

    # Calculate the money exposed to each stock.
    data["exposure_value"] = data["investment"] * data["weight"]

    # Combine the same stock across multiple funds.
    stock_data = data.groupby("stock", as_index=False).agg(
        exposure_value=("exposure_value", "sum"),
        sector=("sector", "first"),
    )

    # Express each stock's exposure as a percentage of the portfolio.
    stock_data["portfolio_weight"] = (
        stock_data["exposure_value"] / total_investment * 100
    )

    return stock_data.sort_values(
        "exposure_value", ascending=False
    ).reset_index(drop=True)


def calculate_fund_overlap(holdings):
    """
    Calculate pairwise stock-allocation overlap for every fund.
    Assumes complete, normalized stock holdings for every fund.
    """

    weights = holdings.pivot_table(
        index="stock",
        columns="fund",
        values="weight",
        aggfunc="sum",
        fill_value=0,
    )

    # Verify that every fund's holdings sum to 100%.
    totals = weights.sum(axis=0)

    if not ((totals - 1.0).abs() < 0.000001).all():
        raise ValueError(
            "Overlap requires complete holdings summing to 100% "
            "for every fund."
        )

    funds = weights.columns
    overlap = pd.DataFrame(
        0.0, index=funds, columns=funds
    )

    for fund_a in funds:
        for fund_b in funds:
            # For each stock, count only the shared allocation.
            shared = weights[[fund_a, fund_b]].min(axis=1).sum()
            overlap.loc[fund_a, fund_b] = shared * 100

    return overlap


def calculate_sector_exposure(stock_data):
    """
    Aggregate stock exposure into business sectors.
    """

    sector_data = stock_data.groupby("sector", as_index=False).agg(
        exposure_value=("exposure_value", "sum")
    )

    total = sector_data["exposure_value"].sum()

    if total > 0:
        sector_data["portfolio_weight"] = (
            sector_data["exposure_value"] / total * 100
        )
    else:
        sector_data["portfolio_weight"] = 0.0

    return sector_data.sort_values(
        "exposure_value", ascending=False
    ).reset_index(drop=True)


def calculate_overlap_details(holdings, fund_a, fund_b):
    """
    Explain which stocks contribute to the overlap
    between two mutual funds.
    """

    available_funds = set(holdings["fund"].unique())

    if fund_a not in available_funds or fund_b not in available_funds:
        raise ValueError("Select two funds with available holdings data.")

    if fund_a == fund_b:
        raise ValueError("Select two different funds to compare.")

    # Get the stock weights for each selected fund.
    weights = holdings.pivot_table(
        index="stock",
        columns="fund",
        values="weight",
        aggfunc="sum",
        fill_value=0,
    )

    # Check that both portfolios are complete.
    for fund in (fund_a, fund_b):
        if abs(weights[fund].sum() - 1.0) >= 0.000001:
            raise ValueError(
                f"{fund} holdings must sum to 100%."
            )

    # Build a comparison table for all stocks in either fund.
    details = pd.DataFrame({
        "Stock": weights.index,
        f"{fund_a} Weight (%)": weights[fund_a].values * 100,
        f"{fund_b} Weight (%)": weights[fund_b].values * 100,
    })

    # Shared allocation is the smaller weight in each stock.
    details["Shared Allocation (%)"] = details[
        [f"{fund_a} Weight (%)", f"{fund_b} Weight (%)"]
    ].min(axis=1)

    # Show the stocks contributing most to overlap first.
    details = details.sort_values(
        "Shared Allocation (%)",
        ascending=False,
    ).reset_index(drop=True)

    total_overlap = details["Shared Allocation (%)"].sum()

    return details, total_overlap


def generate_concentration_alerts(
    stock_data,
    sector_data,
    stock_threshold=20.0,
    sector_threshold=40.0,
):
    """
    Generate educational alerts for concentrated stock
    and sector exposure.

    Thresholds are percentages, such as 20.0 for 20%.
    """

    alerts = []

    # Check individual stock concentration.
    for _, row in stock_data.iterrows():
        weight = row["portfolio_weight"]

        if weight >= stock_threshold:
            alerts.append({
                "Type": "Stock",
                "Name": row["stock"],
                "Exposure (₹)": row["exposure_value"],
                "Portfolio Weight (%)": weight,
                "Message": (
                    f"{row['stock']} accounts for "
                    f"{weight:.2f}% of the analyzed portfolio."
                ),
            })

    # Check sector concentration.
    for _, row in sector_data.iterrows():
        weight = row["portfolio_weight"]

        if weight >= sector_threshold:
            alerts.append({
                "Type": "Sector",
                "Name": row["sector"],
                "Exposure (₹)": row["exposure_value"],
                "Portfolio Weight (%)": weight,
                "Message": (
                    f"The {row['sector']} sector accounts for "
                    f"{weight:.2f}% of the analyzed portfolio."
                ),
            })

    return sorted(
        alerts,
        key=lambda alert: alert["Portfolio Weight (%)"],
        reverse=True,
    )
