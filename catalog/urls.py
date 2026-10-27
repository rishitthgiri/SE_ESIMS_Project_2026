from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.product_list),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<uuid:pk>/edit/', views.product_edit, name='product_edit'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<uuid:pk>/edit/', views.category_edit, name='category_edit'),
]