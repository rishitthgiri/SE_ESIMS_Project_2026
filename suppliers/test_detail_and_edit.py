"""Phase 3 additions for UT-SUP-01 / IT-SUP-02 (FR-015, FR-016): edit page, supplier page, unknown ids."""
import uuid

from django.test import TestCase
from django.urls import reverse

from accounts.testutils import make_admin, make_user
from suppliers.models import Supplier


class SupplierEditAndDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_admin('boss')
        cls.staff = make_user('clerk')
        cls.supplier = Supplier.objects.create(name='Acme Parts', contact='acme@x.com')
        cls.other = Supplier.objects.create(name='Beta Traders', contact='')

    def test_edit_page_shows_current_values(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('suppliers:edit', args=[self.supplier.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Acme Parts')
        self.assertContains(r, 'Edit supplier')

    def test_invalid_edit_keeps_old_values(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('suppliers:edit', args=[self.supplier.pk]), {'name': 'beta traders', 'contact': 'x'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'A supplier with this name already exists.')
        self.supplier.refresh_from_db()
        self.assertEqual((self.supplier.name, self.supplier.contact), ('Acme Parts', 'acme@x.com'))

    def test_unknown_supplier_gives_404(self):
        self.client.force_login(self.admin)
        missing = uuid.uuid4()
        for name in ('edit', 'detail'):
            self.assertEqual(self.client.get(reverse(f'suppliers:{name}', args=[missing])).status_code, 404, name)
        self.assertEqual(self.client.post(reverse('suppliers:disable', args=[missing])).status_code, 404)

    def test_supplier_page_is_admin_only(self):
        url = reverse('suppliers:detail', args=[self.supplier.pk])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn('login', r.url)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Acme Parts')

    def test_disabling_twice_is_harmless(self):
        self.client.force_login(self.admin)
        url = reverse('suppliers:disable', args=[self.other.pk])
        self.client.post(url)
        self.client.post(url)
        self.other.refresh_from_db()
        self.assertEqual(self.other.status, Supplier.Status.DISABLED)

    def test_string_form_is_the_name(self):
        self.assertEqual(str(self.supplier), 'Acme Parts')
        self.assertTrue(self.supplier.is_active)
