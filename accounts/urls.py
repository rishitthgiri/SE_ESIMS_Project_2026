from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.ESIMSLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('staff/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/new/', views.StaffCreateView.as_view(), name='staff_create'),
    path('staff/<int:pk>/edit/', views.StaffUpdateView.as_view(), name='staff_edit'),
    path('staff/<int:pk>/toggle-active/', views.StaffToggleActiveView.as_view(), name='staff_toggle'),
    path('security-log/', views.SecurityLogView.as_view(), name='security_log'),
]
