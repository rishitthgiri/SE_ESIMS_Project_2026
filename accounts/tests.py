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


class PasswordHashingTests(TestCase):
    """ESIMS-03 / SEC-001"""

    def test_password_is_hashed(self):
        user = make_user(password='Plain@Text1')
        self.assertNotEqual(user.password, 'Plain@Text1')
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))

    def test_plaintext_not_in_password_field(self):
        user = make_user(password='Secret@123')
        self.assertNotIn('Secret@123', user.password)

    def test_check_password_works(self):
        user = make_user(password='Secret@123')
        self.assertTrue(user.check_password('Secret@123'))
        self.assertFalse(user.check_password('other'))


class RoleTests(TestCase):
    """ESIMS-04 / FR-002 - Staff vs Admin"""

    def setUp(self):
        self.admin = make_user('admin1', role=User.Role.ADMIN)
        self.staff = make_user('staff1')

    def test_two_roles_exist(self):
        self.assertEqual({r for r, _ in User.Role.choices}, {'STAFF', 'ADMIN'})

    def test_default_role_is_staff(self):
        u = User.objects.create_user('x', 'x@x.com', 'p')
        self.assertEqual(u.role, User.Role.STAFF)

    def test_is_admin_role_property(self):
        self.assertTrue(self.admin.is_admin_role)
        self.assertFalse(self.staff.is_admin_role)

    def test_admin_can_open_staff_list(self):
        self.client.login(username='admin1', password='Pass@12345')
        self.assertEqual(self.client.get(reverse('accounts:staff_list')).status_code, 200)

    def test_staff_gets_403_on_staff_list(self):
        self.client.login(username='staff1', password='Pass@12345')
        self.assertEqual(self.client.get(reverse('accounts:staff_list')).status_code, 403)

    def test_anonymous_redirected_from_staff_list(self):
        r = self.client.get(reverse('accounts:staff_list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('accounts:login'), r.url)

    def test_staff_nav_hides_manage_staff_link(self):
        self.client.login(username='staff1', password='Pass@12345')
        r = self.client.get(reverse('accounts:dashboard'))
        self.assertNotContains(r, 'Manage Staff')
