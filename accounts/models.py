from django.conf import settings
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


class SecurityEvent(models.Model):
    """ESIMS-09 / SEC-006: audit trail of failed logins and blocked access attempts.

    Rows are append-only (never edited). `user` is NULL when the attempt came from
    someone who is not logged in or used an unknown username; the attempted
    username is kept in `username_attempted` either way.
    """

    class EventType(models.TextChoices):
        LOGIN_FAILED = 'LOGIN_FAILED', 'Failed login'
        UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS', 'Unauthorized access attempt'

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='security_events',
    )
    username_attempted = models.CharField(max_length=150, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=255, blank=True)
    details = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp', '-id']
        indexes = [models.Index(fields=['event_type', '-timestamp'])]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('Security events are an audit record and cannot be edited.')
        super().save(*args, **kwargs)

    def __str__(self):
        who = self.username_attempted or (self.user.username if self.user_id else 'anonymous')
        return f'{self.get_event_type_display()} - {who} @ {self.timestamp:%Y-%m-%d %H:%M:%S}'

