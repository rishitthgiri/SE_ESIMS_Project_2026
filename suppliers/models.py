"""Shared supplier model (team contract, see ESIMS_Team8_Agreement.pdf).

Owner: Rishitth (ESIMS-27). "Removing" a supplier means status='disabled'
(soft delete), because old stock-in transactions must keep pointing at it.
"""
import uuid

from django.db import models


class Supplier(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DISABLED = 'disabled', 'Disabled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    contact = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ['name']

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    def __str__(self):
        return self.name
