"""ESIMS-06 / FR-004 / SEC-004: idle sessions expire."""
from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from esims import settings as project_settings

from .testutils import PASSWORD, make_user


class SessionTimeoutConfigTests(TestCase):
    def test_timeout_setting_exists_and_drives_cookie_age(self):
        self.assertGreater(settings.SESSION_TIMEOUT_SECONDS, 0)
        self.assertEqual(settings.SESSION_COOKIE_AGE, settings.SESSION_TIMEOUT_SECONDS)

    def test_timer_resets_on_every_request(self):
        # Without this the timeout would count from login, not from the last activity.
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_session_cookie_is_httponly(self):
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

    def test_int_env_reads_value(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {'SESSION_TIMEOUT_SECONDS': '90'}):
            self.assertEqual(project_settings._int_env('SESSION_TIMEOUT_SECONDS', 1800), 90)

    def test_int_env_falls_back_on_bad_values(self):
        import os
        from unittest import mock
        for bad in ('abc', '', '0', '-5', '1.5'):
            with mock.patch.dict(os.environ, {'SESSION_TIMEOUT_SECONDS': bad}):
                self.assertEqual(project_settings._int_env('SESSION_TIMEOUT_SECONDS', 1800), 1800, bad)

    def test_int_env_default_when_unset(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, clear=False):
            os.environ.pop('SESSION_TIMEOUT_SECONDS', None)
            self.assertEqual(project_settings._int_env('SESSION_TIMEOUT_SECONDS', 1800), 1800)


class SessionTimeoutBehaviourTests(TestCase):
    def setUp(self):
        make_user('staff1')
        self.client.login(username='staff1', password=PASSWORD)

    def _expire_session(self):
        Session.objects.update(expire_date=timezone.now() - timedelta(minutes=1))

    def test_active_session_works(self):
        self.assertEqual(self.client.get(reverse('accounts:dashboard')).status_code, 200)

    def test_idle_session_is_logged_out_and_redirected_to_login(self):
        self._expire_session()
        r = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(r, f"{reverse('accounts:login')}?next=/")

    def test_expired_session_cannot_reach_other_pages(self):
        self._expire_session()
        r = self.client.get(reverse('transactions:list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('accounts:login'), r.url)

    def test_activity_extends_the_session(self):
        Session.objects.update(expire_date=timezone.now() + timedelta(seconds=30))
        self.client.get(reverse('accounts:dashboard'))
        new_expiry = Session.objects.get().expire_date
        self.assertGreater(new_expiry, timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE - 10))

    def test_user_can_log_in_again_after_timeout(self):
        self._expire_session()
        self.client.get(reverse('accounts:dashboard'))
        r = self.client.post(reverse('accounts:login'), {'username': 'staff1', 'password': PASSWORD})
        self.assertRedirects(r, reverse('accounts:dashboard'))
