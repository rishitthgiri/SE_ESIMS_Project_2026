"""Tests for ESIMS-18 to ESIMS-21 (STP IDs in each docstring).

Run:  python manage.py test transactions -v 2
"""
import uuid
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from suppliers.models import Supplier

from . import services
from .models import StockTransaction

User = get_user_model()


class StockTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('staff1', 'staff1@example.com', 'pass12345', role='STAFF')
        cls.admin = User.objects.create_user('admin1', 'admin1@example.com', 'pass12345', role='ADMIN')
        cls.category = Category.objects.create(name='Mobiles')
        cls.supplier = Supplier.objects.create(name='Acme Distributors', contact='acme@example.com')
        cls.product = Product.objects.create(
            sku='MOB-001', name='Phone X', category=cls.category,
            price='19999.00', quantity_in_stock=5, reorder_threshold=2,
        )

    def stock(self, product=None):
        return Product.objects.get(pk=(product or self.product).pk).quantity_in_stock


class StockInServiceTests(StockTestBase):
    def test_stock_in_increases_stock_and_saves_transaction(self):
        """IT-STOCK-01 / FR-010"""
        txn = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=10, user=self.staff)
        self.assertEqual(self.stock(), 15)
        self.assertEqual(txn.transaction_type, StockTransaction.Type.IN)
        self.assertEqual(txn.quantity, 10)
        self.assertEqual(txn.supplier, self.supplier)
        self.assertEqual(txn.user, self.staff)
        self.assertEqual(StockTransaction.objects.count(), 1)

    def test_stock_in_requires_supplier(self):
        """FR-016"""
        with self.assertRaises(services.InvalidStockOperation):
            services.record_stock_in(product=self.product, supplier=None, quantity=1, user=self.staff)
        self.assertEqual(self.stock(), 5)

    def test_stock_in_rejects_bad_quantities(self):
        """SEC-003 (negative tests)"""
        for bad in (0, -3, 'abc', 2.5, None, True, services.MAX_QUANTITY + 1):
            with self.subTest(quantity=bad):
                with self.assertRaises(services.InvalidStockOperation):
                    services.record_stock_in(product=self.product, supplier=self.supplier, quantity=bad, user=self.staff)
        self.assertEqual(self.stock(), 5)
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_stock_in_rejects_disabled_product_and_supplier(self):
        disabled_product = Product.objects.create(
            sku='MOB-002', name='Old Phone', category=self.category, price='100.00',
            quantity_in_stock=1, status=Product.Status.DISABLED,
        )
        with self.assertRaises(services.InvalidStockOperation):
            services.record_stock_in(product=disabled_product, supplier=self.supplier, quantity=1, user=self.staff)
        self.supplier.status = Supplier.Status.DISABLED
        self.supplier.save()
        with self.assertRaises(services.InvalidStockOperation):
            services.record_stock_in(product=self.product, supplier=self.supplier, quantity=1, user=self.staff)


class StockOutServiceTests(StockTestBase):
    def test_stock_out_decreases_stock_and_saves_transaction(self):
        """IT-STOCK-02 / FR-011"""
        txn = services.record_stock_out(product=self.product, quantity=3, user=self.staff)
        self.assertEqual(self.stock(), 2)
        self.assertEqual(txn.transaction_type, StockTransaction.Type.OUT)
        self.assertIsNone(txn.supplier)
        self.assertEqual(StockTransaction.objects.count(), 1)

    def test_reject_over_sale_leaves_stock_unchanged(self):
        """UT-STOCK-02 / FR-012: stock=5, sell 6 -> rejected, stock stays 5"""
        with self.assertRaises(services.InsufficientStock):
            services.record_stock_out(product=self.product, quantity=6, user=self.staff)
        self.assertEqual(self.stock(), 5)
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_selling_exactly_all_stock_is_allowed(self):
        services.record_stock_out(product=self.product, quantity=5, user=self.staff)
        self.assertEqual(self.stock(), 0)
        with self.assertRaises(services.InsufficientStock):
            services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        self.assertEqual(self.stock(), 0)

    def test_stock_out_rejects_bad_quantities_and_disabled_product(self):
        for bad in (0, -1, 'x', 1.5):
            with self.subTest(quantity=bad):
                with self.assertRaises(services.InvalidStockOperation):
                    services.record_stock_out(product=self.product, quantity=bad, user=self.staff)
        self.product.status = Product.Status.DISABLED
        self.product.save()
        with self.assertRaises(services.InvalidStockOperation):
            services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        self.assertEqual(self.stock(), 5)

    def test_failure_after_stock_update_rolls_everything_back(self):
        """Atomicity: stock and history can never diverge (SAD 4.4)"""
        with mock.patch.object(StockTransaction.objects, 'create', side_effect=RuntimeError('boom')):
            with self.assertRaises(RuntimeError):
                services.record_stock_out(product=self.product, quantity=2, user=self.staff)
        self.assertEqual(self.stock(), 5)
        self.assertEqual(StockTransaction.objects.count(), 0)


class TransactionIdAndImmutabilityTests(StockTestBase):
    def test_every_transaction_gets_a_unique_id(self):
        """IT-STOCK-03 / FR-013"""
        a = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=1, user=self.staff)
        b = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=1, user=self.staff)
        c = services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        ids = {a.transaction_id, b.transaction_id, c.transaction_id}
        self.assertEqual(len(ids), 3)
        for i in ids:
            self.assertIsInstance(i, uuid.UUID)

    def test_duplicate_transaction_id_is_blocked_by_database(self):
        a = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=1, user=self.staff)
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockTransaction.objects.create(
                transaction_id=a.transaction_id, product=self.product, supplier=self.supplier,
                user=self.staff, transaction_type='IN', quantity=1,
            )

    def test_transactions_cannot_be_edited_or_deleted(self):
        """Audit history is immutable (SRS section 7)"""
        t = services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        t.quantity = 99
        with self.assertRaises(ValueError):
            t.save()
        with self.assertRaises(ValueError):
            t.delete()

    def test_database_rejects_stock_in_without_supplier(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockTransaction.objects.create(
                product=self.product, supplier=None, user=self.staff,
                transaction_type='IN', quantity=1,
            )


class StockViewTests(StockTestBase):
    def test_pages_require_login(self):
        for name in ('transactions:stock_in', 'transactions:stock_out', 'transactions:list'):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302, name)
            self.assertIn('login', resp['Location'])

    def test_stock_in_form_flow(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('transactions:stock_in')).status_code, 200)
        resp = self.client.post(reverse('transactions:stock_in'), {
            'product': self.product.pk, 'supplier': self.supplier.pk, 'quantity': 4,
        }, follow=True)
        self.assertEqual(self.stock(), 9)
        txn = StockTransaction.objects.get()
        self.assertContains(resp, str(txn.transaction_id))
        self.assertContains(resp, 'Stock-in recorded')

    def test_stock_out_form_flow(self):
        self.client.force_login(self.staff)
        resp = self.client.post(reverse('transactions:stock_out'), {
            'product': self.product.pk, 'quantity': 2,
        }, follow=True)
        self.assertEqual(self.stock(), 3)
        self.assertContains(resp, 'Stock-out recorded')

    def test_over_sale_shows_clear_error_and_changes_nothing(self):
        self.client.force_login(self.staff)
        resp = self.client.post(reverse('transactions:stock_out'), {
            'product': self.product.pk, 'quantity': 6,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Only 5 unit(s)')
        self.assertEqual(self.stock(), 5)
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_invalid_input_is_rejected_by_the_form(self):
        """ST-SEC-03"""
        self.client.force_login(self.staff)
        for bad in ('-5', '0', 'abc', '', '99999999999'):
            with self.subTest(quantity=bad):
                resp = self.client.post(reverse('transactions:stock_out'), {
                    'product': self.product.pk, 'quantity': bad,
                })
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(self.stock(), 5)
        self.assertEqual(StockTransaction.objects.count(), 0)

    def test_dropdowns_only_offer_active_products(self):
        Product.objects.create(sku='MOB-009', name='Hidden Phone', category=self.category,
                               price='1.00', status=Product.Status.DISABLED)
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('transactions:stock_out'))
        self.assertContains(resp, 'MOB-001')
        self.assertNotContains(resp, 'MOB-009')

    def test_staff_see_own_transactions_admin_sees_all(self):
        services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        services.record_stock_out(product=self.product, quantity=1, user=self.admin)
        mine = StockTransaction.objects.get(user=self.staff)
        theirs = StockTransaction.objects.get(user=self.admin)
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('transactions:list'))
        self.assertContains(resp, str(mine.transaction_id))
        self.assertNotContains(resp, str(theirs.transaction_id))
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('transactions:list'))
        self.assertContains(resp, str(mine.transaction_id))
        self.assertContains(resp, str(theirs.transaction_id))

    def test_transaction_list_type_filter(self):
        services.record_stock_in(product=self.product, supplier=self.supplier, quantity=1, user=self.staff)
        services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('transactions:list') + '?type=IN')
        self.assertEqual(len(resp.context['page']), 1)
