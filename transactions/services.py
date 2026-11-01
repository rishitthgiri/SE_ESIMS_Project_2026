"""Stock business logic (ESIMS-18/19/20, hardened in Sprint 2 by ESIMS-23 and ESIMS-25).

Layers inside this module:

1. PURE calculations (`validate_quantity`, `stock_after_in`, `stock_after_out`): no database,
   no request. This is the "stock calculation" that unit tests hit directly (ESIMS-25 / NFR-006).
2. Database services (`record_stock_in`, `record_stock_out`): run inside ONE database
   transaction and lock the product row (select_for_update), so two people selling the last
   unit at the same moment cannot both succeed. If anything fails, stock and history are
   rolled back together (SAD section 4.4).

Double-submit protection (ESIMS-23 / NFR-004): every form carries a one-time `request_token`.
The token is stored on the transaction (unique column). Submitting the same token again does
NOT record anything new; it raises `DuplicateSubmission` carrying the transaction that was
already saved, and the view simply shows that one.
"""
import uuid

from django.db import IntegrityError, transaction

from catalog.models import Product
from suppliers.models import Supplier

from .models import StockTransaction

MAX_QUANTITY = 1_000_000


class StockError(Exception):
    """Base class for all expected stock-rule failures (safe to show to users)."""


class InvalidStockOperation(StockError):
    """Bad input: quantity, product, supplier or form token not usable."""


class InsufficientStock(StockError):
    """Stock-out larger than available stock (FR-012)."""


class DuplicateSubmission(StockError):
    """The same form was submitted twice (NFR-004). `.transaction` is the already-saved record."""

    def __init__(self, existing):
        super().__init__('This transaction was already recorded.')
        self.transaction = existing


# --------------------------------------------------------------------------- pure calculations
def validate_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise InvalidStockOperation('Quantity must be a whole number.')
    if quantity < 1:
        raise InvalidStockOperation('Quantity must be at least 1.')
    if quantity > MAX_QUANTITY:
        raise InvalidStockOperation(f'Quantity cannot exceed {MAX_QUANTITY:,}.')


def stock_after_in(current, quantity):
    """Stock level after a purchase of `quantity` units. Pure function (no database)."""
    validate_quantity(quantity)
    return current + quantity


def stock_after_out(current, quantity, label=''):
    """Stock level after a sale of `quantity` units; refuses to go below zero. Pure function."""
    validate_quantity(quantity)
    if quantity > current:
        of = f' of {label}' if label else ''
        raise InsufficientStock(f'Only {current} unit(s){of} in stock; cannot sell {quantity}.')
    return current - quantity


# --------------------------------------------------------------------------- helpers
def _validate_token(request_token):
    if request_token is not None and not isinstance(request_token, uuid.UUID):
        raise InvalidStockOperation('Invalid form token. Please reload the page and try again.')


def _find_token(request_token):
    if request_token is None:
        return None
    return StockTransaction.objects.filter(request_token=request_token).first()


def _check_duplicate(request_token, *, user, product, transaction_type):
    """Raise DuplicateSubmission if this token was already used by the same user for the same action."""
    existing = _find_token(request_token)
    if existing is None:
        return
    same_action = (
        existing.user_id == user.pk
        and existing.product_id == product.pk
        and existing.transaction_type == transaction_type
    )
    if not same_action:
        # Someone else's token, or reused for a different action: never reveal or reuse it.
        raise InvalidStockOperation('This form was already used. Please reload the page and try again.')
    raise DuplicateSubmission(existing)


def _lock_product(product):
    """Re-read the product with a row lock. Two simultaneous requests for one product queue up here."""
    try:
        return Product.objects.select_for_update().get(pk=product.pk)
    except Product.DoesNotExist:
        raise InvalidStockOperation('Product does not exist.')


def _require_active(product):
    if product.status != Product.Status.ACTIVE:
        raise InvalidStockOperation('This product is disabled and cannot be used in new transactions.')


def _create_transaction(**fields):
    """Insert the history row. A unique-token clash means a concurrent double-submit got past the check."""
    try:
        with transaction.atomic():  # savepoint, so the outer transaction survives an IntegrityError
            return StockTransaction.objects.create(**fields)
    except IntegrityError:
        existing = _find_token(fields.get('request_token'))
        if existing is not None:
            raise DuplicateSubmission(existing)  # outer atomic rolls the stock change back
        raise


# --------------------------------------------------------------------------- database services
@transaction.atomic
def record_stock_in(*, product, supplier, quantity, user, request_token=None):
    """Record a purchase: stock goes UP. Returns the saved StockTransaction.

    Raises DuplicateSubmission if `request_token` was already used for this action.
    """
    validate_quantity(quantity)
    _validate_token(request_token)
    if supplier is None:
        raise InvalidStockOperation('A registered supplier is required for stock-in.')

    locked = _lock_product(product)
    _check_duplicate(request_token, user=user, product=locked, transaction_type=StockTransaction.Type.IN)
    _require_active(locked)
    if not Supplier.objects.filter(pk=supplier.pk, status=Supplier.Status.ACTIVE).exists():
        raise InvalidStockOperation('Supplier is not registered or is disabled.')

    locked.quantity_in_stock = stock_after_in(locked.quantity_in_stock, quantity)
    locked.save(update_fields=['quantity_in_stock'])

    return _create_transaction(
        product=locked,
        supplier=supplier,
        user=user,
        transaction_type=StockTransaction.Type.IN,
        quantity=quantity,
        request_token=request_token,
    )


@transaction.atomic
def record_stock_out(*, product, quantity, user, request_token=None):
    """Record a sale: stock goes DOWN. Rejects the sale if it would go below zero.

    Raises DuplicateSubmission if `request_token` was already used for this action.
    """
    validate_quantity(quantity)
    _validate_token(request_token)

    locked = _lock_product(product)
    _check_duplicate(request_token, user=user, product=locked, transaction_type=StockTransaction.Type.OUT)
    _require_active(locked)

    locked.quantity_in_stock = stock_after_out(locked.quantity_in_stock, quantity, label=locked.sku)
    locked.save(update_fields=['quantity_in_stock'])

    return _create_transaction(
        product=locked,
        supplier=None,
        user=user,
        transaction_type=StockTransaction.Type.OUT,
        quantity=quantity,
        request_token=request_token,
    )
