"""ESIMS-09 / SEC-006: failed logins and unauthorized access attempts are logged."""
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import SecurityEvent
from .testutils import PASSWORD, make_admin, make_user

LOGIN = 'accounts:login'
FAILED = SecurityEvent.EventType.LOGIN_FAILED
DENIED = SecurityEvent.EventType.UNAUTHORIZED_ACCESS


class FailedLoginLoggingTests(TestCase):
    def setUp(self):
        self.user = make_user('staff1')

    def test_wrong_password_is_logged_with_user_ip_and_timestamp(self):
        before = timezone.now()
        self.client.post(reverse(LOGIN), {'username': 'staff1', 'password': 'wrong'})
        ev = SecurityEvent.objects.get()
        self.assertEqual(ev.event_type, FAILED)
        self.assertEqual(ev.user, self.user)
        self.assertEqual(ev.username_attempted, 'staff1')
        self.assertEqual(ev.ip_address, '127.0.0.1')
        self.assertEqual(ev.method, 'POST')
        self.assertEqual(ev.path, reverse(LOGIN))
        self.assertGreaterEqual(ev.timestamp, before)
        self.assertLessEqual(ev.timestamp, timezone.now())

    def test_unknown_username_is_logged_without_a_user(self):
        self.client.post(reverse(LOGIN), {'username': 'ghost', 'password': 'x'})
        ev = SecurityEvent.objects.get()
        self.assertIsNone(ev.user)
        self.assertEqual(ev.username_attempted, 'ghost')

    def test_login_by_email_is_matched_to_the_user(self):
        self.client.post(reverse(LOGIN), {'username': 'staff1@esims.local', 'password': 'wrong'})
        self.assertEqual(SecurityEvent.objects.get().user, self.user)

    def test_deactivated_account_login_attempt_is_logged(self):
        make_user('gone', is_active=False)
        self.client.post(reverse(LOGIN), {'username': 'gone', 'password': PASSWORD})
        ev = SecurityEvent.objects.get()
        self.assertEqual(ev.event_type, FAILED)
        self.assertEqual(ev.username_attempted, 'gone')

    def test_every_failed_attempt_gets_its_own_row(self):
        for _ in range(3):
            self.client.post(reverse(LOGIN), {'username': 'staff1', 'password': 'wrong'})
        self.assertEqual(SecurityEvent.objects.filter(event_type=FAILED).count(), 3)

    def test_successful_login_is_not_logged_as_a_failure(self):
        self.client.post(reverse(LOGIN), {'username': 'staff1', 'password': PASSWORD})
        self.assertEqual(SecurityEvent.objects.count(), 0)

    def test_password_is_never_stored(self):
        self.client.post(reverse(LOGIN), {'username': 'staff1', 'password': 'SuperSecret!1'})
        ev = SecurityEvent.objects.get()
        stored = ' '.join(str(getattr(ev, f.name)) for f in SecurityEvent._meta.fields)
        self.assertNotIn('SuperSecret', stored)

    def test_hostile_username_is_sanitized_before_it_is_stored(self):
        self.client.post(reverse(LOGIN), {'username': 'bob\x00<script>alert(1)</script>\nFAKE', 'password': 'x'})
        ev = SecurityEvent.objects.get()
        self.assertNotIn('\x00', ev.username_attempted)
        self.assertNotIn('<', ev.username_attempted)
        self.assertNotIn('\n', ev.username_attempted)

    def test_very_long_username_is_logged_and_truncated(self):
        # The form rejects >254 chars before authentication; it must still be logged (truncated to 150).
        self.client.post(reverse(LOGIN), {'username': 'a' * 5000, 'password': 'x'})
        ev = SecurityEvent.objects.get()
        self.assertEqual(ev.event_type, FAILED)
        self.assertEqual(len(ev.username_attempted), 150)
        self.assertIn('rejected', ev.details)

    def test_username_that_passes_the_form_but_exceeds_the_column_is_truncated(self):
        self.client.post(reverse(LOGIN), {'username': 'a' * 200, 'password': 'x'})
        self.assertLessEqual(len(SecurityEvent.objects.get().username_attempted), 150)

    def test_wrong_password_is_logged_exactly_once(self):
        self.client.post(reverse(LOGIN), {'username': 'staff1', 'password': 'wrong'})
        self.assertEqual(SecurityEvent.objects.count(), 1)

    def test_blank_form_submit_is_not_logged(self):
        self.client.post(reverse(LOGIN), {'username': '', 'password': ''})
        self.assertEqual(SecurityEvent.objects.count(), 0)

    def test_event_is_also_written_to_the_python_logger(self):
        with self.assertLogs('esims.security', level='WARNING') as cm:
            self.client.post(reverse(LOGIN), {'username': 'staff1', 'password': 'wrong'})
        self.assertIn('LOGIN_FAILED', cm.output[0])
        self.assertIn('staff1', cm.output[0])

    def test_logging_failure_does_not_break_the_login_page(self):
        with mock.patch('accounts.security.SecurityEvent.objects') as manager:
            manager.create.side_effect = RuntimeError('db down')
            with self.assertLogs('esims.security', level='ERROR'):
                r = self.client.post(reverse(LOGIN), {'username': 'staff1', 'password': 'wrong'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Invalid username/email or password.')


class UnauthorizedAccessLoggingTests(TestCase):
    def setUp(self):
        self.staff = make_user('staff1')
        self.admin = make_admin()

    def test_staff_opening_admin_page_is_logged(self):
        self.client.login(username='staff1', password=PASSWORD)
        r = self.client.get(reverse('accounts:staff_list'))
        self.assertEqual(r.status_code, 403)
        ev = SecurityEvent.objects.get()
        self.assertEqual(ev.event_type, DENIED)
        self.assertEqual(ev.user, self.staff)
        self.assertEqual(ev.username_attempted, 'staff1')
        self.assertEqual(ev.path, reverse('accounts:staff_list'))
        self.assertEqual(ev.method, 'GET')
        self.assertIn('STAFF', ev.details)
        self.assertIsNotNone(ev.timestamp)

    def test_blocked_post_is_logged_with_its_method(self):
        self.client.login(username='staff1', password=PASSWORD)
        self.client.post(reverse('accounts:staff_create'), {})
        self.assertEqual(SecurityEvent.objects.get().method, 'POST')

    def test_each_blocked_admin_url_is_logged(self):
        self.client.login(username='staff1', password=PASSWORD)
        for name, args in (('staff_list', []), ('staff_create', []), ('security_log', []),
                           ('staff_edit', [self.admin.pk]), ):
            self.client.get(reverse(f'accounts:{name}', args=args))
        self.assertEqual(SecurityEvent.objects.filter(event_type=DENIED).count(), 4)

    def test_administrator_access_is_not_logged(self):
        self.client.login(username='admin1', password=PASSWORD)
        self.client.get(reverse('accounts:staff_list'))
        self.assertEqual(SecurityEvent.objects.count(), 0)

    def test_normal_staff_pages_are_not_logged(self):
        self.client.login(username='staff1', password=PASSWORD)
        self.client.get(reverse('accounts:dashboard'))
        self.client.get(reverse('transactions:list'))
        self.assertEqual(SecurityEvent.objects.count(), 0)

    def test_anonymous_redirect_to_login_is_routine_and_not_logged(self):
        self.client.get(reverse('accounts:staff_list'))
        self.assertEqual(SecurityEvent.objects.count(), 0)

    def test_denied_event_is_written_to_python_logger(self):
        self.client.login(username='staff1', password=PASSWORD)
        with self.assertLogs('esims.security', level='WARNING') as cm:
            self.client.get(reverse('accounts:staff_list'))
        self.assertIn('UNAUTHORIZED_ACCESS', cm.output[0])


class SecurityLogPageTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        make_user('staff1')
        self.client.post(reverse(LOGIN), {'username': 'staff1', 'password': 'wrong'})       # LOGIN_FAILED
        self.client.login(username='staff1', password=PASSWORD)
        self.client.get(reverse('accounts:staff_list'))                                       # UNAUTHORIZED_ACCESS
        self.client.logout()
        self.client.login(username='admin1', password=PASSWORD)

    def test_admin_sees_events_with_user_and_timestamp(self):
        r = self.client.get(reverse('accounts:security_log'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Failed login')
        self.assertContains(r, 'Unauthorized access attempt')
        self.assertContains(r, 'staff1')
        self.assertContains(r, timezone.now().strftime('%Y-%m-%d'))
        self.assertContains(r, '127.0.0.1')

    def test_newest_event_first(self):
        events = list(self.client.get(reverse('accounts:security_log')).context['events'])
        self.assertEqual([e.event_type for e in events], [DENIED, FAILED])

    def test_filter_by_type(self):
        r = self.client.get(reverse('accounts:security_log') + f'?type={FAILED}')
        self.assertEqual([e.event_type for e in r.context['events']], [FAILED])

    def test_unknown_filter_value_is_ignored(self):
        r = self.client.get(reverse('accounts:security_log') + '?type=<script>')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['events']), 2)
        self.assertNotContains(r, '<script>')

    def test_pagination(self):
        for i in range(30):
            SecurityEvent.objects.create(event_type=FAILED, username_attempted=f'u{i}')
        r = self.client.get(reverse('accounts:security_log'))
        self.assertEqual(len(r.context['events']), 25)
        r2 = self.client.get(reverse('accounts:security_log') + '?page=2')
        self.assertEqual(r2.status_code, 200)

    def test_attacker_text_is_escaped_on_the_page(self):
        SecurityEvent.objects.create(event_type=FAILED, username_attempted='<img src=x onerror=alert(1)>')
        r = self.client.get(reverse('accounts:security_log'))
        self.assertNotContains(r, '<img src=x')

    def test_staff_cannot_read_the_log(self):
        self.client.logout()
        self.client.login(username='staff1', password=PASSWORD)
        self.assertEqual(self.client.get(reverse('accounts:security_log')).status_code, 403)

    def test_dashboard_card_visible_to_admin(self):
        self.assertContains(self.client.get(reverse('accounts:dashboard')), 'Security Log')


class SecurityEventModelTests(TestCase):
    def test_events_cannot_be_edited(self):
        ev = SecurityEvent.objects.create(event_type=FAILED, username_attempted='x')
        ev.details = 'tampered'
        with self.assertRaises(ValueError):
            ev.save()

    def test_event_survives_user_deletion(self):
        u = make_user('temp')
        ev = SecurityEvent.objects.create(event_type=FAILED, user=u, username_attempted='temp')
        u.delete()
        ev.refresh_from_db()
        self.assertIsNone(ev.user)
        self.assertEqual(ev.username_attempted, 'temp')

    def test_str(self):
        ev = SecurityEvent.objects.create(event_type=FAILED, username_attempted='bob')
        self.assertIn('bob', str(ev))
