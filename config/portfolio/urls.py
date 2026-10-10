"""
urls.py — URL patterns for the portfolio app.
Included by config/urls.py via: path('', include('portfolio.urls'))

IMPORTANT: 'export' must come BEFORE '<int:holding_id>' so Django
matches /api/portfolio/export/ first, not as id=export.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard (HTML)
    path('', views.dashboard, name='portfolio_dashboard'),

    # API — stocks catalogue
    path('api/stocks/', views.api_stocks, name='api_stocks'),

    # API — portfolio collection (list + add)
    path('api/portfolio/', views.api_portfolio, name='api_portfolio'),

    # API — CSV export  ← MUST be before <int:holding_id> route
    path('api/portfolio/export/', views.api_portfolio_export, name='api_portfolio_export'),

    # API — individual holding (update / delete)
    path('api/portfolio/<int:holding_id>/', views.api_portfolio_detail, name='api_portfolio_detail'),
]
