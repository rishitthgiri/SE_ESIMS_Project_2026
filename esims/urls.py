
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
 HEAD
    path('catalog/', include('catalog.urls')),

    path('', include('accounts.urls')),
 origin/main
    path('transactions/', include('transactions.urls')),
]