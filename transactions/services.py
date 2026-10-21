"""Stock business logic (ESIMS-18/19/20), independent of views (NFR-006).

Both functions run inside ONE database transaction and lock the product row
(select_for_update), so two people selling the last unit at the same moment
cannot both succeed. If anything fails, stock and history are rolled back
together (SAD section 4.4).
"""
from django.db import transaction

from catalog.models import Product
from suppliers.models import Supplier

from .models import StockTransaction

MAX_QUANTITY = 1_000_000


class StockError(Exception):
    """Base class for all expected stock-rule failures (safe to show to users)."""


class InvalidStockOperation(StockError):
    """Bad input: quantity, product or supplier not usable."""


class InsufficientStock(StockError):
    """Stock-out larger than available stock (FR-012)."""


def validate_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise InvalidStockOperation('Quantity must be a whole number.')
    if quantity < 1:
        raise InvalidStockOperation('Quantity must be at least 1.')
    if quantity > MAX_QUANTITY:
        raise InvalidStockOperation(f'Quantity cannot exceed {MAX_QUANTITY:,}.')


def _lock_active_product(product):
    """Re-read the product with a row lock and make sure it is active."""
    try:
        locked = Product.objects.select_for_update().get(pk=product.pk)
    except Product.DoesNotExist:
        raise InvalidStockOperation('Product does not exist.')
    if locked.status != Product.Status.ACTIVE:
        raise InvalidStockOperation('This product is disabled and cannot be used in new transactions.')
    return locked


@transaction.atomic
def record_stock_in(*, product, supplier, quantity, user, request_token=None):
    """Record a purchase: stock goes UP. Returns the saved StockTransaction."""
    validate_quantity(quantity)
    if supplier is None:
        raise InvalidStockOperation('A registered supplier is required for stock-in.')
    if not Supplier.objects.filter(pk=supplier.pk, status=Supplier.Status.ACTIVE).exists():
        raise InvalidStockOperation('Supplier is not registered or is disabled.')

    locked = _lock_active_product(product)
    locked.quantity_in_stock += quantity
    locked.save(update_fields=['quantity_in_stock'])

    return StockTransaction.objects.create(
        product=locked,
        supplier=supplier,
        user=user,
        transaction_type=StockTransaction.Type.IN,
        quantity=quantity,
        request_token=request_token,
    )


@transaction.atomic
def record_stock_out(*, product, quantity, user, request_token=None):
    """Record a sale: stock goes DOWN. Rejects the sale if it would go below zero."""
    validate_quantity(quantity)

    locked = _lock_active_product(product)
    if quantity > locked.quantity_in_stock:
        raise InsufficientStock(
            f'Only {locked.quantity_in_stock} unit(s) of {locked.sku} in stock; '
            f'cannot sell {quantity}.'
        )
    locked.quantity_in_stock -= quantity
    locked.save(update_fields=['quantity_in_stock'])

    return StockTransaction.objects.create(
        product=locked,
        supplier=None,
        user=user,
        transaction_type=StockTransaction.Type.OUT,
        quantity=quantity,
        request_token=request_token,
    )
