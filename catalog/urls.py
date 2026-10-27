from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<uuid:pk>/edit/', views.category_edit, name='category_edit'),
]