"""Shared catalog models (team contract, see ESIMS_Team8_Agreement.pdf).

Owner: Sakthevel (ESIMS-10/11). Do not rename fields without telling the team,
because stock (transactions), suppliers and reports all depend on them.
"""
import uuid

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DISABLED = 'disabled', 'Disabled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DISABLED = 'disabled', 'Disabled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    # PositiveIntegerField also adds a database CHECK (>= 0): stock can never go negative.
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=0)
    supplier = models.ForeignKey(
        'suppliers.Supplier', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='products',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['status'])]

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    def __str__(self):
        return f'{self.sku} - {self.name}'
