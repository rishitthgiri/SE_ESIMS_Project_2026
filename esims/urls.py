
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('transactions/', include('transactions.urls')),
]

# ESIMS-09: every 403 (Staff opening an admin page, etc.) is logged before the page is shown.
handler403 = 'accounts.views.permission_denied'
