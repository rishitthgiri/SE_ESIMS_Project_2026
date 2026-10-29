"""Security event logging (ESIMS-09 / SEC-006).

Every event is written to the database (viewable by Administrators at /security-log/)
AND to the `esims.security` Python logger (console / log file, see LOGGING in settings).
Logging must never break the request, so all failures are swallowed and reported.
"""
import logging

from esims.validation import sanitize_text

from .models import SecurityEvent

logger = logging.getLogger('esims.security')


def client_ip(request):
    """Use REMOTE_ADDR only. X-Forwarded-For is client-controlled and would be spoofable."""
    return (request.META.get('REMOTE_ADDR') or None) if request is not None else None


def log_security_event(event_type, request=None, *, user=None, username='', details=''):
    username = sanitize_text(username)[:150]
    details = sanitize_text(details)[:255]
    method = sanitize_text(getattr(request, 'method', ''))[:10]
    path = sanitize_text(request.get_full_path() if request is not None else '')[:255]
    ip = client_ip(request)
    if user is not None and not getattr(user, 'pk', None):
        user = None
    if user is not None and not username:
        username = user.get_username()

    logger.warning(
        'security_event type=%s user=%s ip=%s method=%s path=%s details=%s',
        event_type, username or '-', ip or '-', method or '-', path or '-', details or '-',
    )
    try:
        return SecurityEvent.objects.create(
            event_type=event_type, user=user, username_attempted=username,
            ip_address=ip, method=method, path=path, details=details,
        )
    except Exception:  # never let audit logging take the site down
        logger.exception('Could not store security event in the database')
        return None
