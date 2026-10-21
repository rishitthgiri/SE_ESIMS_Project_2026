from django.urls import path

from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list, name='list'),
    path('in/', views.stock_in, name='stock_in'),
    path('out/', views.stock_out, name='stock_out'),
]
