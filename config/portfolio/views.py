"""
views.py — All views for the Stock Portfolio Tracker.

Endpoints:
  GET  /                          → Dashboard HTML page
  GET  /api/stocks/               → List supported stocks + prices
  GET  /api/portfolio/            → List holdings + totals
  POST /api/portfolio/            → Add (or update) a holding
  PATCH/PUT /api/portfolio/<id>/  → Update holding quantity
  DELETE /api/portfolio/<id>/     → Delete a holding
  GET  /api/portfolio/export/     → Download CSV
"""

import csv
import json

from decimal import Decimal, InvalidOperation
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import PortfolioHolding
from .stock_config import all_stocks, get_price, is_valid_symbol, STOCK_COMPANIES


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _holding_to_dict(holding: PortfolioHolding) -> dict:
    """Serialize a PortfolioHolding to a JSON-safe dict."""
    price = get_price(holding.stock_symbol)
    investment_value = price * Decimal(holding.quantity)
    return {
        "id":               holding.id,
        "stock_symbol":     holding.stock_symbol,
        "company_name":     STOCK_COMPANIES.get(holding.stock_symbol, holding.stock_symbol),
        "stock_price":      str(price),
        "quantity":         holding.quantity,
        "investment_value": str(investment_value),
        "created_at":       holding.created_at.strftime("%Y-%m-%d %H:%M"),
        "updated_at":       holding.updated_at.strftime("%Y-%m-%d %H:%M"),
    }


def _parse_json(request) -> tuple[dict | None, JsonResponse | None]:
    """Parse JSON body; return (data, None) on success or (None, error_response)."""
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data, None
    except (json.JSONDecodeError, ValueError):
        return None, JsonResponse(
            {"error": "Invalid JSON in request body."}, status=400
        )


def _validate_quantity(raw_qty) -> tuple[int | None, str | None]:
    """
    Validate raw quantity input.
    Returns (int_qty, None) on success, or (None, error_message) on failure.
    """
    if raw_qty is None:
        return None, "Quantity is required."
    # Reject floats or strings that look like floats
    if isinstance(raw_qty, float):
        return None, "Quantity must be a whole number, not a decimal."
    try:
        qty = int(raw_qty)
    except (ValueError, TypeError):
        return None, "Quantity must be a positive whole number."
    if qty <= 0:
        return None, "Quantity must be greater than zero."
    # Extra guard: reject strings like "5.5"
    if str(raw_qty).strip().find('.') != -1:
        return None, "Quantity must be a whole number, not a decimal."
    return qty, None


# ---------------------------------------------------------------------------
# Dashboard view (renders the HTML page)
# ---------------------------------------------------------------------------

def dashboard(request):
    """Render the main Stock Portfolio Tracker dashboard."""
    stocks = all_stocks()
    return render(request, "portfolio/index.html", {"stocks": stocks})


# ---------------------------------------------------------------------------
# API: Supported stocks
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def api_stocks(request):
    """
    GET /api/stocks/
    Returns the list of supported stock symbols and their sample prices.
    """
    return JsonResponse({"stocks": all_stocks()}, status=200)


# ---------------------------------------------------------------------------
# API: Portfolio collection (list + add)
# ---------------------------------------------------------------------------

@csrf_exempt          # CSRF is handled via the JS X-CSRFToken header in fetch()
@require_http_methods(["GET", "POST"])
def api_portfolio(request):
    if request.method == "GET":
        return _portfolio_list(request)
    return _portfolio_add(request)


def _portfolio_list(request):
    """
    GET /api/portfolio/
    Returns all holdings with per-holding investment values and totals.
    """
    holdings = PortfolioHolding.objects.all()
    holding_data = [_holding_to_dict(h) for h in holdings]

    total_investment = sum(
        Decimal(h["investment_value"]) for h in holding_data
    )
    total_quantity = sum(h["quantity"] for h in holding_data)

    return JsonResponse({
        "holdings":         holding_data,
        "total_investment": str(total_investment),
        "total_stocks":     len(holding_data),
        "total_quantity":   total_quantity,
    }, status=200)


def _portfolio_add(request):
    """
    POST /api/portfolio/
    Body: {"stock_symbol": "AAPL", "quantity": 5}

    If a holding for that symbol already exists, the quantity is ADDED
    to the existing row (no duplicate rows created).
    """
    data, err = _parse_json(request)
    if err:
        return err

    symbol = str(data.get("stock_symbol", "")).strip().upper()
    raw_qty = data.get("quantity")

    if not symbol:
        return JsonResponse({"error": "stock_symbol is required."}, status=400)

    if not is_valid_symbol(symbol):
        return JsonResponse(
            {"error": f"'{symbol}' is not a supported stock symbol. "
                      f"Supported: {', '.join(sorted(STOCK_COMPANIES.keys()))}."},
            status=400,
        )

    qty, qty_err = _validate_quantity(raw_qty)
    if qty_err:
        return JsonResponse({"error": qty_err}, status=400)

    # Upsert: update quantity if symbol already exists, otherwise create.
    holding, created = PortfolioHolding.objects.get_or_create(
        stock_symbol=symbol,
        defaults={"quantity": qty},
    )
    if not created:
        holding.quantity += qty
        holding.save()

    action = "added" if created else "quantity updated"
    return JsonResponse({
        "message": f"Stock {action} successfully.",
        "holding": _holding_to_dict(holding),
    }, status=201 if created else 200)


# ---------------------------------------------------------------------------
# API: Portfolio item (update + delete)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["GET", "PATCH", "PUT", "DELETE"])
def api_portfolio_detail(request, holding_id):
    """
    PATCH/PUT /api/portfolio/<id>/  → set (replace) the quantity
    DELETE    /api/portfolio/<id>/  → remove the holding
    """
    try:
        holding = PortfolioHolding.objects.get(pk=holding_id)
    except PortfolioHolding.DoesNotExist:
        return JsonResponse(
            {"error": f"No holding found with id={holding_id}."}, status=404
        )

    if request.method in ("PATCH", "PUT"):
        return _portfolio_update(request, holding)
    if request.method == "DELETE":
        return _portfolio_delete(holding)
    # GET — return single holding detail
    return JsonResponse({"holding": _holding_to_dict(holding)}, status=200)


def _portfolio_update(request, holding: PortfolioHolding):
    """
    PATCH /api/portfolio/<id>/
    Body: {"quantity": 10}
    Replaces (not adds) the quantity of an existing holding.
    """
    data, err = _parse_json(request)
    if err:
        return err

    raw_qty = data.get("quantity")
    qty, qty_err = _validate_quantity(raw_qty)
    if qty_err:
        return JsonResponse({"error": qty_err}, status=400)

    holding.quantity = qty
    holding.save()

    return JsonResponse({
        "message": "Holding updated successfully.",
        "holding": _holding_to_dict(holding),
    }, status=200)


def _portfolio_delete(holding: PortfolioHolding):
    """DELETE /api/portfolio/<id>/"""
    symbol = holding.stock_symbol
    holding.delete()
    return JsonResponse(
        {"message": f"Holding for {symbol} deleted successfully."}, status=200
    )


# ---------------------------------------------------------------------------
# API: CSV export
# ---------------------------------------------------------------------------

@require_http_methods(["GET"])
def api_portfolio_export(request):
    """
    GET /api/portfolio/export/
    Returns a CSV file with all holdings and a total row.
    """
    holdings = PortfolioHolding.objects.all()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="portfolio.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Stock Symbol", "Company Name", "Stock Price (USD)",
        "Quantity", "Investment Value (USD)", "Date Added",
    ])

    total = Decimal("0.00")
    for h in holdings:
        price = get_price(h.stock_symbol)
        inv   = price * Decimal(h.quantity)
        total += inv
        writer.writerow([
            h.stock_symbol,
            STOCK_COMPANIES.get(h.stock_symbol, h.stock_symbol),
            f"{price:.2f}",
            h.quantity,
            f"{inv:.2f}",
            h.created_at.strftime("%Y-%m-%d"),
        ])

    # Total row
    writer.writerow([])
    writer.writerow(["", "", "", "TOTAL INVESTMENT", f"{total:.2f}", ""])
    writer.writerow(["", "", "", "(Sample prices — not live market data)", "", ""])

    return response
