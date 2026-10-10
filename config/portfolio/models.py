from django.db import models
from django.contrib.auth.models import User


class Stock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=20)
    company_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    purchase_date = models.DateField()

    def investment_value(self):
        return self.quantity * self.purchase_price

    def current_value(self):
        return self.quantity * self.current_price

    def profit_loss(self):
        return self.current_value() - self.investment_value()

    def __str__(self):
        return self.stock_symbol


# ---------------------------------------------------------------------------
# PortfolioHolding — used by the Stock Portfolio Tracker feature.
#
# Design notes:
#   • Only stock_symbol + quantity are stored. The stock price is NEVER stored
#     here; it is always looked up from portfolio.stock_config.STOCK_PRICES.
#   • stock_symbol is unique so that adding the same stock twice just increases
#     the quantity of the existing row (no duplicates).
#   • No user FK right now (no auth system). Adding one later is a single
#     migration: add `user = ForeignKey(User, …)` and run makemigrations.
# ---------------------------------------------------------------------------
class PortfolioHolding(models.Model):
    stock_symbol = models.CharField(max_length=10, unique=True)
    quantity     = models.PositiveIntegerField()
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['stock_symbol']
        verbose_name        = 'Portfolio Holding'
        verbose_name_plural = 'Portfolio Holdings'

    def __str__(self):
        return f"{self.stock_symbol} × {self.quantity}"