from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """ESIMS user. Two roles: Staff and Administrator (ESIMS-04 / FR-002)."""

    class Role(models.TextChoices):
        STAFF = 'STAFF', 'Staff'
        ADMIN = 'ADMIN', 'Administrator'

    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
