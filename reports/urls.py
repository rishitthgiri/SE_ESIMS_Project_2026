from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('low-stock/', views.low_stock, name='low_stock'),
    path('sales/', views.sales_report, name='sales'),
    path('top-selling/', views.top_selling, name='top_selling'),
]
