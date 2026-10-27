from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from transactions import services
from transactions.models import StockTransaction

from .models import Supplier

User = get_user_model()


class SupplierBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user('boss', 'boss@x.com', 'pw12345!', role=User.Role.ADMIN)
        cls.staff = User.objects.create_user('clerk', 'clerk@x.com', 'pw12345!', role=User.Role.STAFF)
        cls.supplier = Supplier.objects.create(name='Acme Parts', contact='acme@x.com')
        cat = Category.objects.create(name='Phones')
        cls.product = Product.objects.create(
            sku='P1', name='Phone', category=cat, price='100.00', reorder_threshold=5,
        )


class SupplierCrudTests(SupplierBase):
    def test_admin_can_add_supplier(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('suppliers:add'), {'name': 'NewCo', 'contact': '123'})
        self.assertRedirects(resp, reverse('suppliers:list'))
        self.assertTrue(Supplier.objects.filter(name='NewCo', status='active').exists())

    def test_blank_name_rejected(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('suppliers:add'), {'name': '   ', 'contact': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Supplier.objects.count(), 1)

    def test_duplicate_name_rejected_case_insensitive(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('suppliers:add'), {'name': 'acme parts', 'contact': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Supplier.objects.count(), 1)

    def test_admin_can_edit_supplier(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('suppliers:edit', args=[self.supplier.pk]), {'name': 'Acme Ltd', 'contact': 'new'})
        self.supplier.refresh_from_db()
        self.assertEqual((self.supplier.name, self.supplier.contact), ('Acme Ltd', 'new'))

    def test_edit_keeping_same_name_is_allowed(self):
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('suppliers:edit', args=[self.supplier.pk]), {'name': 'Acme Parts', 'contact': 'x'})
        self.assertRedirects(resp, reverse('suppliers:list'))

    def test_disable_is_soft_delete(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('suppliers:disable', args=[self.supplier.pk]))
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.status, 'disabled')
        self.assertTrue(Supplier.objects.filter(pk=self.supplier.pk).exists())

    def test_disable_requires_post(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('suppliers:disable', args=[self.supplier.pk]))
        self.assertEqual(resp.status_code, 405)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.status, 'active')

    def test_list_filter_by_status(self):
        Supplier.objects.create(name='Old Co', status='disabled')
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('suppliers:list'), {'status': 'disabled'})
        self.assertContains(resp, 'Old Co')
        self.assertNotContains(resp, 'Acme Parts')


class SupplierPermissionTests(SupplierBase):
    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse('suppliers:list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_staff_get_403_everywhere(self):
        self.client.force_login(self.staff)
        pk = self.supplier.pk
        for name, args in [('list', []), ('add', []), ('edit', [pk]), ('detail', [pk])]:
            self.assertEqual(self.client.get(reverse(f'suppliers:{name}', args=args)).status_code, 403, name)
        self.assertEqual(self.client.post(reverse('suppliers:disable', args=[pk])).status_code, 403)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.status, 'active')


class SupplierStockLinkTests(SupplierBase):
    """ESIMS-28: stock-in is linked to a supplier and visible."""

    def test_stock_in_is_linked_to_supplier_and_shown_on_supplier_page(self):
        txn = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=7, user=self.staff)
        self.assertEqual(txn.supplier, self.supplier)
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('suppliers:detail', args=[self.supplier.pk]))
        self.assertContains(resp, str(txn.transaction_id))

    def test_stock_out_not_listed_on_supplier_page(self):
        services.record_stock_in(product=self.product, supplier=self.supplier, quantity=7, user=self.staff)
        out = services.record_stock_out(product=self.product, quantity=2, user=self.staff)
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('suppliers:detail', args=[self.supplier.pk]))
        self.assertNotContains(resp, str(out.transaction_id))

    def test_supplier_shown_on_transaction_list(self):
        services.record_stock_in(product=self.product, supplier=self.supplier, quantity=3, user=self.admin)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('transactions:list')), 'Acme Parts')

    def test_disabled_supplier_cannot_be_used_for_stock_in(self):
        self.supplier.status = 'disabled'
        self.supplier.save()
        with self.assertRaises(services.InvalidStockOperation):
            services.record_stock_in(product=self.product, supplier=self.supplier, quantity=1, user=self.staff)
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_disabled_supplier_history_is_kept(self):
        services.record_stock_in(product=self.product, supplier=self.supplier, quantity=3, user=self.admin)
        self.client.force_login(self.admin)
        self.client.post(reverse('suppliers:disable', args=[self.supplier.pk]))
        self.assertEqual(StockTransaction.objects.filter(supplier=self.supplier).count(), 1)
