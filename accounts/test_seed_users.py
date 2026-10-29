"""The shared demo-user seed: one login for every role."""
import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from .testutils import User

ADMIN_PW = 'Admin@12345'
STAFF_PW = 'Staff@12345'


def seed(*args, **kwargs):
    out = StringIO()
    call_command('seed_demo_users', *args, stdout=out, **kwargs)
    return out.getvalue()


@override_settings(DEBUG=True)
class SeedDemoUsersTests(TestCase):
    def test_creates_every_kind_of_user(self):
        seed()
        self.assertEqual(User.objects.count(), 5)
        admin = User.objects.get(username='admin')
        manager = User.objects.get(username='manager')
        staff1 = User.objects.get(username='staff1')
        inactive = User.objects.get(username='inactive_staff')
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_superuser and admin.is_staff)
        self.assertEqual(manager.role, User.Role.ADMIN)
        self.assertFalse(manager.is_superuser)
        self.assertTrue(manager.is_admin_role)
        self.assertEqual(staff1.role, User.Role.STAFF)
        self.assertFalse(staff1.is_admin_role)
        self.assertFalse(inactive.is_active)

    def test_passwords_are_stored_hashed(self):
        seed()
        for u in User.objects.all():
            self.assertTrue(u.password.startswith('pbkdf2_sha256$'), u.username)

    def test_each_seeded_user_can_log_in_except_the_deactivated_one(self):
        seed()
        for username, pw in (('admin', ADMIN_PW), ('manager', ADMIN_PW), ('staff1', STAFF_PW), ('staff2', STAFF_PW)):
            with self.subTest(user=username):
                self.client.logout()
                r = self.client.post(reverse('accounts:login'), {'username': username, 'password': pw})
                self.assertRedirects(r, reverse('accounts:dashboard'))
        self.client.logout()
        r = self.client.post(reverse('accounts:login'), {'username': 'inactive_staff', 'password': STAFF_PW})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_by_email_works_for_seeded_users(self):
        seed()
        r = self.client.post(reverse('accounts:login'), {'username': 'staff1@esims.local', 'password': STAFF_PW})
        self.assertRedirects(r, reverse('accounts:dashboard'))

    def test_roles_behave_correctly_in_the_app(self):
        seed()
        self.client.login(username='manager', password=ADMIN_PW)
        self.assertEqual(self.client.get(reverse('accounts:staff_list')).status_code, 200)
        self.client.logout()
        self.client.login(username='staff1', password=STAFF_PW)
        self.assertEqual(self.client.get(reverse('accounts:staff_list')).status_code, 403)

    def test_safe_to_run_twice(self):
        seed()
        out = seed()
        self.assertEqual(User.objects.count(), 5)
        self.assertIn('skipped', out)

    def test_rerun_does_not_touch_existing_users(self):
        seed()
        u = User.objects.get(username='staff1')
        u.set_password('Changed@999')
        u.save()
        seed()
        self.assertTrue(User.objects.get(username='staff1').check_password('Changed@999'))

    def test_reset_restores_demo_state(self):
        seed()
        u = User.objects.get(username='staff1')
        u.set_password('Changed@999')
        u.role = User.Role.ADMIN
        u.is_active = False
        u.save()
        seed('--reset')
        u.refresh_from_db()
        self.assertTrue(u.check_password(STAFF_PW))
        self.assertEqual(u.role, User.Role.STAFF)
        self.assertTrue(u.is_active)

    def test_reset_does_not_create_duplicates(self):
        seed()
        seed('--reset')
        self.assertEqual(User.objects.count(), 5)

    def test_password_override_from_environment(self):
        with mock.patch.dict(os.environ, {'ESIMS_SEED_PASSWORD': 'Team@Pass1'}):
            seed()
        self.assertTrue(User.objects.get(username='staff1').check_password('Team@Pass1'))
        self.assertTrue(User.objects.get(username='admin').check_password('Team@Pass1'))

    def test_existing_user_with_same_email_is_not_overwritten(self):
        User.objects.create_user('someone', email='staff1@esims.local', password='x')
        out = seed()
        self.assertIn('skipped', out)
        self.assertFalse(User.objects.filter(username='staff1').exists())

    def test_output_lists_usernames_and_passwords(self):
        out = seed()
        for text in ('admin', 'manager', 'staff1', 'staff2', 'inactive_staff', ADMIN_PW, STAFF_PW):
            self.assertIn(text, out)


class SeedSafetyTests(TestCase):
    @override_settings(DEBUG=False)
    def test_refuses_to_run_when_debug_is_off(self):
        with self.assertRaises(CommandError):
            seed()
        self.assertEqual(User.objects.count(), 0)

    @override_settings(DEBUG=False)
    def test_force_overrides_the_debug_guard(self):
        seed('--force')
        self.assertEqual(User.objects.count(), 5)
