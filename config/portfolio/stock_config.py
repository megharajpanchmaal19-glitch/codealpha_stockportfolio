"""
stock_config.py — Centralized stock price configuration.

These are SAMPLE / DEMO prices only — NOT live market data.
All investment calculations on the backend use these values exclusively.
The frontend never supplies a price that the backend trusts.
"""

from decimal import Decimal

# ------------------------------------------------------------------
# Sample stock prices (INR / ₹) — manually defined for demonstration.
# To add a new stock, add its symbol here. The frontend will pick
# it up automatically from the /api/stocks/ endpoint.
# ------------------------------------------------------------------
STOCK_PRICES: dict[str, Decimal] = {
    "AAPL":  Decimal("180.00"),
    "TSLA":  Decimal("250.00"),
    "GOOGL": Decimal("150.00"),
    "MSFT":  Decimal("420.00"),
    "AMZN":  Decimal("190.00"),
    "NVDA":  Decimal("120.00"),
    "META":  Decimal("500.00"),
}

# Human-readable company names (used in the frontend display)
STOCK_COMPANIES: dict[str, str] = {
    "AAPL":  "Apple Inc.",
    "TSLA":  "Tesla Inc.",
    "GOOGL": "Alphabet Inc.",
    "MSFT":  "Microsoft Corporation",
    "AMZN":  "Amazon.com Inc.",
    "NVDA":  "NVIDIA Corporation",
    "META":  "Meta Platforms Inc.",
}


def get_price(symbol: str) -> Decimal | None:
    """Return the configured price for a symbol, or None if unknown."""
    return STOCK_PRICES.get(symbol.upper())


def is_valid_symbol(symbol: str) -> bool:
    """Return True if the symbol is in the supported stock list."""
    return symbol.upper() in STOCK_PRICES


def all_stocks() -> list[dict]:
    """Return a list of dicts describing every supported stock."""
    result = []
    for symbol, price in STOCK_PRICES.items():
        result.append({
            "symbol":       symbol,
            "company_name": STOCK_COMPANIES.get(symbol, symbol),
            "price":        str(price),
        })
    return result
