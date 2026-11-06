"""Catalog write operations that do not belong in HTTP handlers."""
from .models import Product


def disable_product(product):
    """Disable a product without changing its stock or its related history."""
    if not product.is_active:
        return False
    product.status = Product.Status.DISABLED
    product.save(update_fields=['status'])
    return True
