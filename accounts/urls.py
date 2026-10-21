from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.ESIMSLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('staff/', views.StaffListView.as_view(), name='staff_list'),
]
