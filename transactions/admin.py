from django.contrib import admin

from .models import StockTransaction


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    """Read-only: transactions are an audit record and must not be edited here."""
    list_display = ('transaction_id', 'transaction_type', 'product', 'quantity', 'supplier', 'user', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('product__sku', 'product__name')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
