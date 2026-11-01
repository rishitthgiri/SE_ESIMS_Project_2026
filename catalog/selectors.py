"""Read and filter catalog products for views and management commands."""
import uuid

from django.db.models import Q

from .models import Product


def search_products(q='', category='', status=''):
    """Return products matching the catalog search and filter values."""
    products = Product.objects.select_related('category', 'supplier').all()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    if category:
        try:
            category_id = uuid.UUID(category)
        except (ValueError, TypeError, AttributeError):
            pass
        else:
            products = products.filter(category_id=category_id)

    if status in (Product.Status.ACTIVE, Product.Status.DISABLED):
        products = products.filter(status=status)
    return products
