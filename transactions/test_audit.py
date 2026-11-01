"""ESIMS-22: audit trail (FR-014, ST-STOCK-04). Run: python manage.py test transactions.test_audit -v 2"""
from datetime import timedelta

from django.contrib import admin as django_admin
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from accounts.models import SecurityEvent
from catalog.models import Category, Product

from . import services
from .admin import StockTransactionAdmin
from .models import StockTransaction
from .testutils import StockTestBase


class AuditRecordTests(StockTestBase):
    def test_every_transaction_stores_user_timestamp_and_quantity(self):
        """ST-STOCK-04 / FR-014: user, timestamp and quantity are present on every record"""
        before = timezone.now() - timedelta(seconds=5)
        a = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=7, user=self.staff)
        b = services.record_stock_out(product=self.product, quantity=3, user=self.admin)
        for txn, user, qty in ((a, self.staff, 7), (b, self.admin, 3)):
            txn.refresh_from_db()
            self.assertEqual(txn.user, user)
            self.assertEqual(txn.quantity, qty)
            self.assertIsNotNone(txn.timestamp)
            self.assertGreaterEqual(txn.timestamp, before)
            self.assertLessEqual(txn.timestamp, timezone.now())

    def test_audit_records_cannot_be_edited_or_deleted(self):
        """FR-014: records are immutable"""
        txn = services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        txn.quantity = 99
        with self.assertRaises(ValueError):
            txn.save()
        with self.assertRaises(ValueError):
            txn.delete()
        txn.refresh_from_db()
        self.assertEqual(txn.quantity, 1)

    def test_django_admin_screen_is_read_only(self):
        request = RequestFactory().get('/admin/')
        request.user = self.admin
        model_admin = StockTransactionAdmin(StockTransaction, django_admin.site)
        txn = services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request, txn))
        self.assertFalse(model_admin.has_delete_permission(request, txn))


class AuditAccessTests(StockTestBase):
    def test_admin_can_open_audit_list_and_sees_everyones_transactions(self):
        mine = services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        theirs = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=2, user=self.admin)
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('transactions:audit'))
        self.assertEqual(resp.status_code, 200)
        for txn in (mine, theirs):
            self.assertContains(resp, str(txn.transaction_id))
        self.assertContains(resp, 'staff1')
        self.assertContains(resp, 'admin1')
        self.assertContains(resp, 'cannot be edited or deleted')

    def test_staff_get_403_and_the_attempt_is_logged(self):
        """SEC-002 + SEC-006: Staff cannot open the audit list"""
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('transactions:audit'))
        self.assertEqual(resp.status_code, 403)
        event = SecurityEvent.objects.get(event_type=SecurityEvent.EventType.UNAUTHORIZED_ACCESS)
        self.assertEqual(event.user, self.staff)
        self.assertEqual(event.path, '/transactions/audit/')

    def test_logged_out_visitor_is_sent_to_login(self):
        resp = self.client.get(reverse('transactions:audit'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_audit_page_cannot_change_data(self):
        """Read-only: POST/PUT/DELETE are not allowed"""
        txn = services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        self.client.force_login(self.admin)
        url = reverse('transactions:audit')
        self.assertEqual(self.client.post(url, {'quantity': 99}).status_code, 405)
        self.assertEqual(self.client.delete(url).status_code, 405)
        txn.refresh_from_db()
        self.assertEqual(txn.quantity, 1)
        self.assertEqual(StockTransaction.objects.count(), 1)


class AuditFilterTests(StockTestBase):
    def setUp(self):
        self.phone_in = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=4, user=self.admin)
        self.phone_out = services.record_stock_out(product=self.product, quantity=2, user=self.staff)
        laptop = Product.objects.create(
            sku='LAP-777', name='Laptop Pro', category=Category.objects.get(name='Mobiles'),
            price='55000.00', quantity_in_stock=10, reorder_threshold=1)
        self.laptop_out = services.record_stock_out(product=laptop, quantity=1, user=self.staff)
        self.client.force_login(self.admin)

    def ids(self, **params):
        resp = self.client.get(reverse('transactions:audit'), params)
        self.assertEqual(resp.status_code, 200)
        return {t.pk for t in resp.context['transactions']}, resp

    def test_filter_by_type(self):
        ids, _ = self.ids(type='IN')
        self.assertEqual(ids, {self.phone_in.pk})
        ids, _ = self.ids(type='OUT')
        self.assertEqual(ids, {self.phone_out.pk, self.laptop_out.pk})

    def test_filter_by_user(self):
        ids, _ = self.ids(user='admin')
        self.assertEqual(ids, {self.phone_in.pk})

    def test_filter_by_product_sku_or_name(self):
        ids, _ = self.ids(q='LAP-777')
        self.assertEqual(ids, {self.laptop_out.pk})
        ids, _ = self.ids(q='phone x')
        self.assertEqual(ids, {self.phone_in.pk, self.phone_out.pk})

    def test_filter_by_transaction_id(self):
        ids, _ = self.ids(q=str(self.phone_out.transaction_id))
        self.assertEqual(ids, {self.phone_out.pk})

    def test_filter_by_date_range(self):
        old = timezone.now() - timedelta(days=10)
        StockTransaction.objects.filter(pk=self.phone_in.pk).update(timestamp=old)   # back-date one record
        today = timezone.localdate().isoformat()
        ids, _ = self.ids(start=today)
        self.assertEqual(ids, {self.phone_out.pk, self.laptop_out.pk})
        ids, _ = self.ids(end=(timezone.localdate() - timedelta(days=5)).isoformat())
        self.assertEqual(ids, {self.phone_in.pk})

    def test_backwards_date_range_shows_error_and_no_rows(self):
        ids, resp = self.ids(start='2026-10-30', end='2026-10-01')
        self.assertEqual(ids, set())
        self.assertContains(resp, 'start date must be on or before')

    def test_garbage_filter_input_is_rejected_safely(self):
        for params in ({'start': 'not-a-date'}, {'type': 'HACK'}, {'user': 'x' * 500}):
            ids, resp = self.ids(**params)
            self.assertEqual(ids, set(), params)

    def test_pagination_keeps_filters(self):
        for _ in range(30):
            services.record_stock_in(product=self.product, supplier=self.supplier, quantity=1, user=self.admin)
        resp = self.client.get(reverse('transactions:audit'), {'type': 'IN'})
        self.assertEqual(len(resp.context['transactions']), 25)
        self.assertContains(resp, 'type=IN&page=2')
        resp = self.client.get(reverse('transactions:audit'), {'type': 'IN', 'page': 2})
        self.assertEqual(len(resp.context['transactions']), 6)   # 31 stock-ins in total
