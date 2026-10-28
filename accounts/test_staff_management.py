"""ESIMS-05 / FR-003 / UC-10: Admin manages Staff accounts."""
from django.test import TestCase
from django.urls import reverse

from .testutils import PASSWORD, User, make_admin, make_user

STRONG = 'Str0ng@Pass99'


def create_payload(**overrides):
    data = {
        'username': 'newstaff', 'email': 'new@esims.local',
        'first_name': 'New', 'last_name': 'Staff',
        'password1': STRONG, 'password2': STRONG,
    }
    data.update(overrides)
    return data


class StaffManagementTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.client.login(username='admin1', password=PASSWORD)

    # ---- create
    def test_admin_creates_staff(self):
        r = self.client.post(reverse('accounts:staff_create'), create_payload())
        self.assertRedirects(r, reverse('accounts:staff_list'))
        u = User.objects.get(username='newstaff')
        self.assertEqual(u.role, User.Role.STAFF)
        self.assertTrue(u.is_active)
        self.assertTrue(u.password.startswith('pbkdf2_sha256$'))   # ESIMS-03: hashed
        self.assertTrue(u.check_password(STRONG))

    def test_created_staff_can_log_in(self):
        self.client.post(reverse('accounts:staff_create'), create_payload())
        self.client.logout()
        r = self.client.post(reverse('accounts:login'), {'username': 'newstaff', 'password': STRONG})
        self.assertRedirects(r, reverse('accounts:dashboard'))

    def test_create_form_cannot_make_an_administrator(self):
        self.client.post(reverse('accounts:staff_create'), create_payload(role='ADMIN', is_superuser='on', is_staff='on'))
        u = User.objects.get(username='newstaff')
        self.assertEqual(u.role, User.Role.STAFF)
        self.assertFalse(u.is_superuser)
        self.assertFalse(u.is_staff)

    def test_create_rejects_duplicate_email(self):
        make_user('existing', email='dup@esims.local')
        r = self.client.post(reverse('accounts:staff_create'), create_payload(email='dup@esims.local'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='newstaff').exists())

    def test_create_rejects_duplicate_email_ignoring_case(self):
        make_user('existing', email='dup@esims.local')
        r = self.client.post(reverse('accounts:staff_create'), create_payload(email='DUP@Esims.Local'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='newstaff').exists())

    def test_create_rejects_duplicate_username_ignoring_case(self):
        make_user('existing')
        r = self.client.post(reverse('accounts:staff_create'), create_payload(username='EXISTING'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(User.objects.filter(username__iexact='existing').count(), 1)

    def test_create_rejects_password_mismatch(self):
        r = self.client.post(reverse('accounts:staff_create'), create_payload(password2='different'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='newstaff').exists())

    def test_create_rejects_weak_password(self):
        r = self.client.post(reverse('accounts:staff_create'), create_payload(password1='12345678', password2='12345678'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='newstaff').exists())

    def test_email_is_stored_lowercase(self):
        self.client.post(reverse('accounts:staff_create'), create_payload(email='Mixed@Esims.Local'))
        self.assertEqual(User.objects.get(username='newstaff').email, 'mixed@esims.local')

    # ---- list
    def test_list_shows_only_staff_accounts(self):
        make_user('s1')
        r = self.client.get(reverse('accounts:staff_list'))
        self.assertContains(r, 's1')
        self.assertNotContains(r, 'admin1@esims.local')

    # ---- edit
    def test_admin_edits_staff(self):
        s = make_user('s2')
        r = self.client.post(reverse('accounts:staff_edit', args=[s.pk]), {
            'username': 's2', 'email': 's2@esims.local', 'first_name': 'Changed', 'last_name': 'Name',
        })
        self.assertRedirects(r, reverse('accounts:staff_list'))
        s.refresh_from_db()
        self.assertEqual((s.first_name, s.last_name), ('Changed', 'Name'))

    def test_edit_keeps_password_and_role(self):
        s = make_user('s2')
        old_hash = s.password
        self.client.post(reverse('accounts:staff_edit', args=[s.pk]), {
            'username': 's2', 'email': 's2@esims.local', 'first_name': 'X', 'last_name': 'Y',
            'role': 'ADMIN', 'password': 'hacked',
        })
        s.refresh_from_db()
        self.assertEqual(s.password, old_hash)
        self.assertEqual(s.role, User.Role.STAFF)

    def test_edit_rejects_email_used_by_someone_else(self):
        make_user('other', email='taken@esims.local')
        s = make_user('s3')
        r = self.client.post(reverse('accounts:staff_edit', args=[s.pk]), {
            'username': 's3', 'email': 'TAKEN@esims.local', 'first_name': '', 'last_name': '',
        })
        self.assertEqual(r.status_code, 200)
        s.refresh_from_db()
        self.assertEqual(s.email, 's3@esims.local')

    def test_edit_allows_keeping_own_email(self):
        s = make_user('s4')
        r = self.client.post(reverse('accounts:staff_edit', args=[s.pk]), {
            'username': 's4', 'email': 's4@esims.local', 'first_name': 'Same', 'last_name': 'Email',
        })
        self.assertRedirects(r, reverse('accounts:staff_list'))

    def test_cannot_edit_administrator_through_staff_endpoint(self):
        r = self.client.get(reverse('accounts:staff_edit', args=[self.admin.pk]))
        self.assertEqual(r.status_code, 404)

    # ---- deactivate / reactivate
    def test_admin_deactivates_staff(self):
        s = make_user('s5')
        self.client.post(reverse('accounts:staff_toggle', args=[s.pk]))
        s.refresh_from_db()
        self.assertFalse(s.is_active)

    def test_deactivated_user_cannot_log_in(self):
        s = make_user('s6')
        self.client.post(reverse('accounts:staff_toggle', args=[s.pk]))
        self.client.logout()
        r = self.client.post(reverse('accounts:login'), {'username': 's6', 'password': PASSWORD})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Invalid username/email or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_deactivated_user_cannot_log_in_with_email_either(self):
        s = make_user('s7')
        self.client.post(reverse('accounts:staff_toggle', args=[s.pk]))
        self.client.logout()
        self.client.post(reverse('accounts:login'), {'username': 's7@esims.local', 'password': PASSWORD})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_deactivating_kicks_out_an_already_logged_in_user(self):
        s = make_user('s8')
        staff_client = self.client_class()
        staff_client.login(username='s8', password=PASSWORD)
        self.assertEqual(staff_client.get(reverse('accounts:dashboard')).status_code, 200)
        self.client.post(reverse('accounts:staff_toggle', args=[s.pk]))
        r = staff_client.get(reverse('accounts:dashboard'))
        self.assertRedirects(r, f"{reverse('accounts:login')}?next=/")

    def test_admin_can_reactivate_staff(self):
        s = make_user('s9', is_active=False)
        self.client.post(reverse('accounts:staff_toggle', args=[s.pk]))
        s.refresh_from_db()
        self.assertTrue(s.is_active)
        self.client.logout()
        r = self.client.post(reverse('accounts:login'), {'username': 's9', 'password': PASSWORD})
        self.assertRedirects(r, reverse('accounts:dashboard'))

    def test_toggle_requires_post(self):
        s = make_user('s10')
        self.assertEqual(self.client.get(reverse('accounts:staff_toggle', args=[s.pk])).status_code, 405)
        s.refresh_from_db()
        self.assertTrue(s.is_active)

    def test_cannot_deactivate_administrator_through_staff_endpoint(self):
        r = self.client.post(reverse('accounts:staff_toggle', args=[self.admin.pk]))
        self.assertEqual(r.status_code, 404)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
