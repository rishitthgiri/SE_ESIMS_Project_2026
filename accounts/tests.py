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


class LoginTests(TestCase):
    """ESIMS-02 / FR-001 / UC-01"""

    def setUp(self):
        self.user = make_user()
        self.url = reverse('accounts:login')

    def test_login_page_loads(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_login_with_username(self):
        r = self.client.post(self.url, {'username': 'staff1', 'password': 'Pass@12345'})
        self.assertRedirects(r, reverse('accounts:dashboard'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_with_email(self):
        r = self.client.post(self.url, {'username': 'staff1@esims.local', 'password': 'Pass@12345'})
        self.assertRedirects(r, reverse('accounts:dashboard'))

    def test_login_wrong_password_shows_error(self):
        r = self.client.post(self.url, {'username': 'staff1', 'password': 'wrong'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Invalid username/email or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_unknown_user(self):
        r = self.client.post(self.url, {'username': 'nobody', 'password': 'x'})
        self.assertContains(r, 'Invalid username/email or password.')

    def test_dashboard_requires_login(self):
        r = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(r, f"{reverse('accounts:login')}?next=/")

    def test_logout(self):
        self.client.login(username='staff1', password='Pass@12345')
        self.client.post(reverse('accounts:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)
