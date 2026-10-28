"""ESIMS-07 / SEC-002: Staff are blocked from admin-only pages (and cannot change data through them)."""
from django.test import TestCase
from django.urls import get_resolver, reverse

from . import urls as accounts_urls
from .testutils import PASSWORD, User, make_admin, make_user

# Every URL name in accounts that is NOT admin-only. Anything else MUST be admin-only and listed below.
OPEN_TO_ALL_LOGGED_IN = {'dashboard', 'login', 'logout'}


class AdminOnlyUrlsTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.staff = make_user('staff1')
        self.target = make_user('target')
        # (url name, args, methods to try)
        self.admin_only = [
            ('staff_list', [], ['get']),
            ('staff_create', [], ['get', 'post']),
            ('staff_edit', [self.target.pk], ['get', 'post']),
            ('staff_toggle', [self.target.pk], ['post']),
            ('security_log', [], ['get']),
        ]

    def _call(self, client, method, name, args):
        return getattr(client, method)(reverse(f'accounts:{name}', args=args))

    def test_every_non_public_accounts_url_is_listed_as_admin_only(self):
        """Guard: adding a new accounts URL forces you to decide (and test) whether it is admin-only."""
        names = {p.name for p in accounts_urls.urlpatterns}
        listed = {name for name, _, _ in self.admin_only}
        self.assertEqual(names - OPEN_TO_ALL_LOGGED_IN, listed)

    def test_staff_gets_403_on_every_admin_only_url(self):
        self.client.login(username='staff1', password=PASSWORD)
        for name, args, methods in self.admin_only:
            for method in methods:
                with self.subTest(url=name, method=method):
                    self.assertEqual(self._call(self.client, method, name, args).status_code, 403)

    def test_anonymous_is_redirected_to_login_on_every_admin_only_url(self):
        for name, args, methods in self.admin_only:
            for method in methods:
                with self.subTest(url=name, method=method):
                    r = self._call(self.client, method, name, args)
                    self.assertEqual(r.status_code, 302)
                    self.assertTrue(r.url.startswith(reverse('accounts:login')))

    def test_administrator_is_allowed_on_every_admin_only_url(self):
        self.client.login(username='admin1', password=PASSWORD)
        for name, args, methods in self.admin_only:
            with self.subTest(url=name):
                r = self._call(self.client, methods[0], name, args)
                self.assertEqual(r.status_code, 200 if methods[0] == 'get' else 302)

    def test_403_page_does_not_leak_admin_content(self):
        self.client.login(username='staff1', password=PASSWORD)
        r = self.client.get(reverse('accounts:staff_list'))
        self.assertContains(r, 'Access denied', status_code=403)
        self.assertNotContains(r, 'target@esims.local', status_code=403)

    def test_staff_cannot_create_accounts_by_posting_directly(self):
        self.client.login(username='staff1', password=PASSWORD)
        before = User.objects.count()
        self.client.post(reverse('accounts:staff_create'), {
            'username': 'sneaky', 'email': 'sneaky@esims.local',
            'password1': 'Str0ng@Pass99', 'password2': 'Str0ng@Pass99',
        })
        self.assertEqual(User.objects.count(), before)

    def test_staff_cannot_deactivate_or_edit_other_accounts(self):
        self.client.login(username='staff1', password=PASSWORD)
        self.client.post(reverse('accounts:staff_toggle', args=[self.target.pk]))
        self.client.post(reverse('accounts:staff_edit', args=[self.target.pk]), {
            'username': 'target', 'email': 'target@esims.local', 'first_name': 'Hacked', 'last_name': '',
        })
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.assertEqual(self.target.first_name, '')

    def test_staff_cannot_promote_themselves_to_administrator(self):
        self.client.login(username='staff1', password=PASSWORD)
        self.client.post(reverse('accounts:staff_edit', args=[self.staff.pk]), {
            'username': 'staff1', 'email': 'staff1@esims.local', 'role': 'ADMIN', 'is_superuser': 'on',
        })
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.role, User.Role.STAFF)
        self.assertFalse(self.staff.is_superuser)

    def test_django_admin_site_is_closed_to_staff(self):
        self.client.login(username='staff1', password=PASSWORD)
        r = self.client.get('/admin/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/admin/login/', r.url)

    def test_administrator_role_without_superuser_still_blocked_from_django_admin_site(self):
        self.client.login(username='admin1', password=PASSWORD)   # role ADMIN, not is_staff
        r = self.client.get('/admin/')
        self.assertEqual(r.status_code, 302)


class SharedPagesStayOpenToStaffTests(TestCase):
    """Blocking admin pages must not lock Staff out of the pages they are meant to use."""

    def setUp(self):
        make_user('staff1')
        self.client.login(username='staff1', password=PASSWORD)

    def test_staff_can_open_dashboard(self):
        self.assertEqual(self.client.get(reverse('accounts:dashboard')).status_code, 200)

    def test_staff_can_open_transactions(self):
        self.assertEqual(self.client.get(reverse('transactions:list')).status_code, 200)

    def test_staff_dashboard_hides_admin_cards(self):
        r = self.client.get(reverse('accounts:dashboard'))
        self.assertNotContains(r, 'Manage Staff')
        self.assertNotContains(r, 'Security Log')
