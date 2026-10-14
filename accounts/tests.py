from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


def make_user(username='staff1', password='Pass@12345', role=None, **extra):
    role = role or User.Role.STAFF
    extra.setdefault('email', f'{username}@esims.local')
    return User.objects.create_user(username=username, password=password, role=role, **extra)


class UserModelTests(TestCase):
    """ESIMS-01: project skeleton works (custom user model + DB)."""

    def test_create_user(self):
        u = make_user('first')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(u.role, User.Role.STAFF)

    def test_email_is_unique(self):
        make_user('a', email='same@esims.local')
        with self.assertRaises(Exception):
            make_user('b', email='same@esims.local')
