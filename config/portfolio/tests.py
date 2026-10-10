"""
tests.py — Test suite for the Stock Portfolio Tracker.

Run with:
    python manage.py test portfolio

Uses Django's test client which uses a temporary test database,
so your real stockportfolio database is never touched.
"""

import json
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from .models import PortfolioHolding
from .stock_config import (
    STOCK_PRICES, all_stocks, get_price, is_valid_symbol
)


# ---------------------------------------------------------------------------
# 1. Stock config unit tests
# ---------------------------------------------------------------------------

class StockConfigTests(TestCase):
    """Test the stock_config helpers independently."""

    def test_supported_stocks_returned(self):
        """Retrieving supported stocks returns all defined symbols."""
        stocks = all_stocks()
        symbols = [s["symbol"] for s in stocks]
        self.assertIn("AAPL", symbols)
        self.assertIn("TSLA", symbols)
        self.assertIn("NVDA", symbols)
        self.assertEqual(len(stocks), len(STOCK_PRICES))

    def test_get_price_known_symbol(self):
        price = get_price("AAPL")
        self.assertEqual(price, Decimal("180.00"))

    def test_get_price_case_insensitive(self):
        self.assertEqual(get_price("aapl"), get_price("AAPL"))

    def test_get_price_unknown_symbol_returns_none(self):
        self.assertIsNone(get_price("INVALID"))

    def test_is_valid_symbol_true(self):
        self.assertTrue(is_valid_symbol("MSFT"))

    def test_is_valid_symbol_false(self):
        self.assertFalse(is_valid_symbol("XYZ"))


# ---------------------------------------------------------------------------
# 2. API: /api/stocks/
# ---------------------------------------------------------------------------

class ApiStocksTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_get_stocks_returns_200(self):
        """GET /api/stocks/ returns HTTP 200."""
        response = self.client.get("/api/stocks/")
        self.assertEqual(response.status_code, 200)

    def test_get_stocks_returns_json(self):
        response = self.client.get("/api/stocks/")
        data = json.loads(response.content)
        self.assertIn("stocks", data)
        self.assertIsInstance(data["stocks"], list)

    def test_get_stocks_contains_all_symbols(self):
        response = self.client.get("/api/stocks/")
        data = json.loads(response.content)
        symbols = [s["symbol"] for s in data["stocks"]]
        for sym in STOCK_PRICES:
            self.assertIn(sym, symbols)

    def test_stock_entry_has_price_field(self):
        response = self.client.get("/api/stocks/")
        data = json.loads(response.content)
        for stock in data["stocks"]:
            self.assertIn("price", stock)
            self.assertIn("symbol", stock)


# ---------------------------------------------------------------------------
# 3. API: GET /api/portfolio/ — empty portfolio
# ---------------------------------------------------------------------------

class EmptyPortfolioTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_empty_portfolio_returns_200(self):
        response = self.client.get("/api/portfolio/")
        self.assertEqual(response.status_code, 200)

    def test_empty_portfolio_holdings_list(self):
        response = self.client.get("/api/portfolio/")
        data = json.loads(response.content)
        self.assertEqual(data["holdings"], [])
        self.assertEqual(data["total_stocks"], 0)
        self.assertEqual(data["total_quantity"], 0)
        self.assertEqual(Decimal(data["total_investment"]), Decimal("0"))


# ---------------------------------------------------------------------------
# 4. API: POST /api/portfolio/ — adding a valid holding
# ---------------------------------------------------------------------------

class AddHoldingTests(TestCase):

    def setUp(self):
        self.client = Client()

    def _post(self, payload):
        return self.client.post(
            "/api/portfolio/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_add_valid_stock_returns_201(self):
        response = self._post({"stock_symbol": "AAPL", "quantity": 5})
        self.assertEqual(response.status_code, 201)

    def test_add_valid_stock_creates_db_row(self):
        self._post({"stock_symbol": "AAPL", "quantity": 5})
        self.assertEqual(PortfolioHolding.objects.count(), 1)

    def test_add_valid_stock_correct_investment_value(self):
        """Investment value = 180 × 5 = 900."""
        response = self._post({"stock_symbol": "AAPL", "quantity": 5})
        data = json.loads(response.content)
        self.assertEqual(Decimal(data["holding"]["investment_value"]), Decimal("900.00"))

    def test_add_valid_stock_correct_price_in_response(self):
        """Backend must return the configured price, not a client-supplied one."""
        response = self._post({"stock_symbol": "TSLA", "quantity": 2})
        data = json.loads(response.content)
        self.assertEqual(Decimal(data["holding"]["stock_price"]), Decimal("250.00"))

    def test_add_multiple_stocks_correct_total(self):
        """AAPL×5 + TSLA×2 + MSFT×3 = 900+500+1260 = 2660."""
        self._post({"stock_symbol": "AAPL", "quantity": 5})
        self._post({"stock_symbol": "TSLA", "quantity": 2})
        self._post({"stock_symbol": "MSFT", "quantity": 3})
        response = self.client.get("/api/portfolio/")
        data = json.loads(response.content)
        self.assertEqual(Decimal(data["total_investment"]), Decimal("2660.00"))
        self.assertEqual(data["total_stocks"], 3)
        self.assertEqual(data["total_quantity"], 10)


# ---------------------------------------------------------------------------
# 5. Duplicate stock — quantity must be summed, not duplicated
# ---------------------------------------------------------------------------

class DuplicateStockTests(TestCase):

    def setUp(self):
        self.client = Client()

    def _post(self, payload):
        return self.client.post(
            "/api/portfolio/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_duplicate_stock_upserts_quantity(self):
        """Adding AAPL twice must merge into one row."""
        self._post({"stock_symbol": "AAPL", "quantity": 5})
        self._post({"stock_symbol": "AAPL", "quantity": 2})
        self.assertEqual(PortfolioHolding.objects.count(), 1)
        holding = PortfolioHolding.objects.get(stock_symbol="AAPL")
        self.assertEqual(holding.quantity, 7)

    def test_duplicate_stock_investment_correct(self):
        """After upsert: AAPL×7 = 1260."""
        self._post({"stock_symbol": "AAPL", "quantity": 5})
        self._post({"stock_symbol": "AAPL", "quantity": 2})
        response = self.client.get("/api/portfolio/")
        data = json.loads(response.content)
        self.assertEqual(Decimal(data["total_investment"]), Decimal("1260.00"))


# ---------------------------------------------------------------------------
# 6. Validation — reject invalid inputs
# ---------------------------------------------------------------------------

class ValidationTests(TestCase):

    def setUp(self):
        self.client = Client()

    def _post(self, payload):
        return self.client.post(
            "/api/portfolio/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_reject_invalid_stock_symbol(self):
        response = self._post({"stock_symbol": "FAKE", "quantity": 1})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_reject_missing_stock_symbol(self):
        response = self._post({"quantity": 5})
        self.assertEqual(response.status_code, 400)

    def test_reject_zero_quantity(self):
        response = self._post({"stock_symbol": "AAPL", "quantity": 0})
        self.assertEqual(response.status_code, 400)

    def test_reject_negative_quantity(self):
        response = self._post({"stock_symbol": "AAPL", "quantity": -3})
        self.assertEqual(response.status_code, 400)

    def test_reject_fractional_quantity_float(self):
        response = self._post({"stock_symbol": "AAPL", "quantity": 2.5})
        self.assertEqual(response.status_code, 400)

    def test_reject_missing_quantity(self):
        response = self._post({"stock_symbol": "AAPL"})
        self.assertEqual(response.status_code, 400)

    def test_reject_malformed_json(self):
        response = self.client.post(
            "/api/portfolio/",
            data="not json at all",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_client_supplied_price_is_ignored(self):
        """
        Even if the client sends a 'stock_price' field, the backend must
        always use the configured price.  AAPL = 180, never whatever the
        client sends.
        """
        response = self._post({
            "stock_symbol": "AAPL",
            "quantity": 1,
            "stock_price": 9999,   # adversarial input
        })
        # Request should succeed...
        self.assertIn(response.status_code, [200, 201])
        data = json.loads(response.content)
        # ...but use the configured price, not 9999
        self.assertEqual(Decimal(data["holding"]["stock_price"]), Decimal("180.00"))
        self.assertEqual(Decimal(data["holding"]["investment_value"]), Decimal("180.00"))


# ---------------------------------------------------------------------------
# 7. Update holding (PATCH)
# ---------------------------------------------------------------------------

class UpdateHoldingTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.holding = PortfolioHolding.objects.create(
            stock_symbol="MSFT", quantity=3
        )

    def _patch(self, holding_id, payload):
        return self.client.patch(
            f"/api/portfolio/{holding_id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_update_quantity_returns_200(self):
        response = self._patch(self.holding.id, {"quantity": 10})
        self.assertEqual(response.status_code, 200)

    def test_update_quantity_persisted(self):
        self._patch(self.holding.id, {"quantity": 10})
        self.holding.refresh_from_db()
        self.assertEqual(self.holding.quantity, 10)

    def test_update_investment_value_recalculated(self):
        """After update, investment = 420 × 10 = 4200."""
        response = self._patch(self.holding.id, {"quantity": 10})
        data = json.loads(response.content)
        self.assertEqual(Decimal(data["holding"]["investment_value"]), Decimal("4200.00"))

    def test_update_zero_quantity_rejected(self):
        response = self._patch(self.holding.id, {"quantity": 0})
        self.assertEqual(response.status_code, 400)

    def test_update_nonexistent_holding_returns_404(self):
        response = self._patch(99999, {"quantity": 5})
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# 8. Delete holding
# ---------------------------------------------------------------------------

class DeleteHoldingTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.holding = PortfolioHolding.objects.create(
            stock_symbol="GOOGL", quantity=4
        )

    def test_delete_returns_200(self):
        response = self.client.delete(f"/api/portfolio/{self.holding.id}/")
        self.assertEqual(response.status_code, 200)

    def test_delete_removes_row(self):
        self.client.delete(f"/api/portfolio/{self.holding.id}/")
        self.assertFalse(
            PortfolioHolding.objects.filter(pk=self.holding.id).exists()
        )

    def test_delete_nonexistent_returns_404(self):
        response = self.client.delete("/api/portfolio/99999/")
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# 9. CSV export
# ---------------------------------------------------------------------------

class CsvExportTests(TestCase):

    def setUp(self):
        self.client = Client()
        PortfolioHolding.objects.create(stock_symbol="AAPL", quantity=5)
        PortfolioHolding.objects.create(stock_symbol="TSLA", quantity=2)

    def test_export_returns_200(self):
        response = self.client.get("/api/portfolio/export/")
        self.assertEqual(response.status_code, 200)

    def test_export_content_type_csv(self):
        response = self.client.get("/api/portfolio/export/")
        self.assertIn("text/csv", response["Content-Type"])

    def test_export_contains_holdings(self):
        response = self.client.get("/api/portfolio/export/")
        content = response.content.decode("utf-8")
        self.assertIn("AAPL", content)
        self.assertIn("TSLA", content)

    def test_export_total_correct(self):
        """900 + 500 = 1400."""
        response = self.client.get("/api/portfolio/export/")
        content = response.content.decode("utf-8")
        self.assertIn("1400.00", content)
