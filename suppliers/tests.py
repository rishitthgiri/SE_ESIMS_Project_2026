from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Supplier

User = get_user_model()


def make_user(username, role):
    return User.objects.create_user(
        username=username, password='Pass@12345', email=f'{username}@esims.local', role=role)


class SupplierViewTests(TestCase):
    def setUp(self):
        self.admin = make_user('admin1', User.Role.ADMIN)
        self.staff = make_user('staff1', User.Role.STAFF)
        self.supplier = Supplier.objects.create(name='Acme Traders', contact='9999999999')

    def login(self, user):
        self.client.force_login(user)

    def test_admin_sees_list(self):
        self.login(self.admin)
        r = self.client.get(reverse('suppliers:list'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Acme Traders')

    def test_admin_can_add(self):
        self.login(self.admin)
        r = self.client.post(reverse('suppliers:add'), {'name': 'New Co', 'contact': 'a@b.com'})
        self.assertRedirects(r, reverse('suppliers:list'))
        self.assertTrue(Supplier.objects.filter(name='New Co', status='active').exists())

    def test_add_requires_name(self):
        self.login(self.admin)
        r = self.client.post(reverse('suppliers:add'), {'name': '   ', 'contact': 'x'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Supplier.objects.count(), 1)

    def test_admin_can_edit(self):
        self.login(self.admin)
        url = reverse('suppliers:edit', args=[self.supplier.pk])
        self.client.post(url, {'name': 'Acme Renamed', 'contact': '111'})
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.name, 'Acme Renamed')

    def test_disable_is_soft_delete(self):
        self.login(self.admin)
        self.client.post(reverse('suppliers:disable', args=[self.supplier.pk]))
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.status, Supplier.Status.DISABLED)
        self.assertTrue(Supplier.objects.filter(pk=self.supplier.pk).exists())

    def test_disable_needs_post(self):
        self.login(self.admin)
        r = self.client.get(reverse('suppliers:disable', args=[self.supplier.pk]))
        self.assertEqual(r.status_code, 405)

    def test_staff_blocked_everywhere(self):
        self.login(self.staff)
        pk = self.supplier.pk
        for name, args in [('list', []), ('add', []), ('edit', [pk])]:
            r = self.client.get(reverse(f'suppliers:{name}', args=args))
            self.assertEqual(r.status_code, 302, name)
        r = self.client.post(reverse('suppliers:disable', args=[pk]))
        self.assertEqual(r.status_code, 302)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.status, Supplier.Status.ACTIVE)

    def test_anonymous_redirected(self):
        r = self.client.get(reverse('suppliers:list'))
        self.assertEqual(r.status_code, 302)
