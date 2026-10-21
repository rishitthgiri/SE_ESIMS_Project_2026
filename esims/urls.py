from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('suppliers/', include('suppliers.urls')),
    path('transactions/', include('transactions.urls')),
]
