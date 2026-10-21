"""Stock transactions (ESIMS-18 stock-in, ESIMS-19 stock-out, ESIMS-21 unique ID).

Owner: Samiksha. One row = one stock-in (purchase) or stock-out (sale).
History is immutable: rows are never edited or deleted (SRS section 7).
"""
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class StockTransaction(models.Model):
    class Type(models.TextChoices):
        IN = 'IN', 'Stock-in'
        OUT = 'OUT', 'Stock-out'

    # FR-013: unique ID on every transaction.
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT, related_name='transactions')
    # Required for stock-in (FR-016), empty for stock-out.
    supplier = models.ForeignKey(
        'suppliers.Supplier', null=True, blank=True,
        on_delete=models.PROTECT, related_name='transactions',
    )
    # FR-014 audit data: who, when, how many.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_transactions')
    transaction_type = models.CharField(max_length=3, choices=Type.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    # Reserved for ESIMS-23 (double-submit protection, Sprint 2). Unused in Sprint 1.
    request_token = models.UUIDField(null=True, blank=True, unique=True, editable=False)

    class Meta:
        ordering = ['-timestamp', '-id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='stocktxn_quantity_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(transaction_type='OUT') | models.Q(supplier__isnull=False),
                name='stocktxn_in_requires_supplier',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('Stock transactions are immutable and cannot be edited.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Stock transactions are kept for audit and cannot be deleted.')

    def __str__(self):
        return f'{self.get_transaction_type_display()} {self.quantity} x {self.product_id} ({self.transaction_id})'
