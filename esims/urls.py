from django.contrib import admin
from django.urls import include, path

from .health import health

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health, name='health'),
    path('catalog/', include('catalog.urls')),
    path('', include('accounts.urls')),
    path('transactions/', include('transactions.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('reports/', include('reports.urls')),
]

# ESIMS-09: every 403 (Staff opening an admin page, etc.) is logged before the page is shown.
handler403 = 'accounts.views.permission_denied'