"""Low-stock rule (SRS FR-017). Computed from Product; no extra table in v1.0."""
from django.db.models import F

from catalog.models import Product


def is_low_stock(product):
    """Strictly below the reorder threshold."""
    return product.quantity_in_stock < product.reorder_threshold


def low_stock_products():
    """Active products below their reorder threshold, most urgent first."""
    return (
        Product.objects.filter(status=Product.Status.ACTIVE, quantity_in_stock__lt=F('reorder_threshold'))
        .select_related('category', 'supplier')
        .order_by('quantity_in_stock', 'name')
    )
