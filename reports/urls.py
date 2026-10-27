from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('low-stock/', views.low_stock, name='low_stock'),
]
