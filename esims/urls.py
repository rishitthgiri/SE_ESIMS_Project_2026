from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('catalog/', include('catalog.urls')),
    path('', include('accounts.urls')),
    path('transactions/', include('transactions.urls')),
]