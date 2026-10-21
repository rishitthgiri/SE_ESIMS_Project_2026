from django.urls import path

from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.supplier_list, name='list'),
    path('add/', views.supplier_add, name='add'),
    path('<uuid:pk>/edit/', views.supplier_edit, name='edit'),
    path('<uuid:pk>/disable/', views.supplier_disable, name='disable'),
]
