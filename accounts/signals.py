from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

from esims.validation import sanitize_text

from .models import SecurityEvent
from .security import log_security_event


@receiver(user_login_failed, dispatch_uid='esims_log_failed_login')
def log_failed_login(sender, credentials=None, request=None, **kwargs):
    """ESIMS-09: every failed login is logged with the attempted username, time and IP."""
    User = get_user_model()
    attempted = sanitize_text((credentials or {}).get('username', ''))[:150]
    user = None
    if attempted:
        user = (
            User.objects.filter(username__iexact=attempted).first()
            or User.objects.filter(email__iexact=attempted).first()
        )
    log_security_event(
        SecurityEvent.EventType.LOGIN_FAILED, request,
        user=user, username=attempted, details='Invalid credentials or deactivated account',
    )
