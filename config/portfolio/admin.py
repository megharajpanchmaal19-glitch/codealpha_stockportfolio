from django.contrib import admin
from .models import Stock, PortfolioHolding


@admin.register(PortfolioHolding)
class PortfolioHoldingAdmin(admin.ModelAdmin):
    list_display  = ('stock_symbol', 'quantity', 'created_at', 'updated_at')
    list_filter   = ('stock_symbol',)
    search_fields = ('stock_symbol',)
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(Stock)