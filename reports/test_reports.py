"""ESIMS-31 (FR-018, ST-REPORT-01) and ESIMS-32 (FR-019, ST-REPORT-02)."""
import csv
import io
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.testutils import make_admin, make_user
from catalog.models import Category, Product
from suppliers.models import Supplier
from transactions import services as stock
from transactions.models import StockTransaction

from . import services


def make_product(sku, name, price='10.00', qty=100, threshold=5):
    cat, _ = Category.objects.get_or_create(name='Phones')
    return Product.objects.create(
        sku=sku, name=name, category=cat, price=price, quantity_in_stock=qty, reorder_threshold=threshold)


def sell(product, quantity, user, days_ago=0):
    """Record a real sale, then move its timestamp (history is immutable, so use update())."""
    txn = stock.record_stock_out(product=product, quantity=quantity, user=user)
    StockTransaction.objects.filter(pk=txn.pk).update(timestamp=timezone.now() - timedelta(days=days_ago))
    return txn


def buy(product, quantity, user, supplier, days_ago=0):
    txn = stock.record_stock_in(product=product, supplier=supplier, quantity=quantity, user=user)
    StockTransaction.objects.filter(pk=txn.pk).update(timestamp=timezone.now() - timedelta(days=days_ago))
    return txn


class ReportBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_admin('boss')
        cls.staff = make_user('clerk')
        cls.supplier = Supplier.objects.create(name='Acme')
        cls.today = timezone.localdate()


class ReportAccessTests(ReportBase):
    urls = ['reports:sales', 'reports:top_selling']

    def test_anonymous_redirected_to_login(self):
        for name in self.urls:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn('login', r.url)

    def test_staff_gets_403(self):
        self.client.force_login(self.staff)
        for name in self.urls:
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_staff_cannot_export_csv(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse('reports:sales'), {'export': 'sales'})
        self.assertEqual(r.status_code, 403)

    def test_admin_gets_200(self):
        self.client.force_login(self.admin)
        for name in self.urls:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)


class SalesReportTests(ReportBase):
    def setUp(self):
        self.p = make_product('P-1', 'Phone', price='250.50')
        self.client.force_login(self.admin)

    def test_default_range_is_last_30_days(self):
        sell(self.p, 2, self.staff, days_ago=0)
        sell(self.p, 7, self.staff, days_ago=40)
        r = self.client.get(reverse('reports:sales'))
        self.assertEqual(r.context['totals']['units'], 2)
        self.assertEqual(len(r.context['sales']), 1)

    def test_amount_is_quantity_times_price_and_totals_add_up(self):
        sell(self.p, 2, self.staff)
        sell(self.p, 3, self.staff)
        r = self.client.get(reverse('reports:sales'))
        self.assertEqual(r.context['totals']['units'], 5)
        self.assertEqual(r.context['totals']['amount'], Decimal('1252.50'))
        self.assertContains(r, '1252.50')

    def test_start_and_end_dates_are_inclusive(self):
        d = self.today
        sell(self.p, 1, self.staff, days_ago=10)
        sell(self.p, 2, self.staff, days_ago=5)
        sell(self.p, 4, self.staff, days_ago=1)
        r = self.client.get(reverse('reports:sales'), {
            'start': (d - timedelta(days=5)).isoformat(), 'end': (d - timedelta(days=5)).isoformat()})
        self.assertEqual(r.context['totals']['units'], 2)
        r = self.client.get(reverse('reports:sales'), {'start': (d - timedelta(days=10)).isoformat()})
        self.assertEqual(r.context['totals']['units'], 7)

    def test_stock_in_is_not_a_sale(self):
        buy(self.p, 50, self.staff, self.supplier)
        r = self.client.get(reverse('reports:sales'))
        self.assertEqual(r.context['totals']['units'], 0)
        self.assertContains(r, 'No sales in this date range.')

    def test_sales_table_has_required_columns(self):
        txn = sell(self.p, 1, self.staff)
        r = self.client.get(reverse('reports:sales'))
        for text in ('Transaction reference', 'Quantity sold', 'Sale amount', 'Staff member', str(txn.transaction_id), 'clerk'):
            self.assertContains(r, text)

    def test_start_after_end_is_rejected(self):
        r = self.client.get(reverse('reports:sales'), {'start': '2026-10-20', 'end': '2026-10-01'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'The start date must be on or before the end date.')
        self.assertNotIn('sales', r.context)

    def test_garbage_date_is_rejected(self):
        r = self.client.get(reverse('reports:sales'), {'start': 'not-a-date'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('sales', r.context)

    def test_stock_section_value_and_movement(self):
        buy(self.p, 30, self.staff, self.supplier)       # stock 130
        sell(self.p, 10, self.staff)                     # stock 120
        sell(self.p, 5, self.staff, days_ago=60)         # outside the default range
        r = self.client.get(reverse('reports:sales'))
        row = [x for x in r.context['stock'] if x.pk == self.p.pk][0]
        self.assertEqual(row.quantity_in_stock, 115)
        self.assertEqual(row.stock_value, Decimal('115') * Decimal('250.50'))
        self.assertEqual((row.units_in, row.units_out), (30, 10))
        self.assertEqual(r.context['stock_total'], Decimal('115') * Decimal('250.50'))

    def test_empty_database_still_renders(self):
        StockTransaction.objects.all()  # none
        Product.objects.all().delete()
        r = self.client.get(reverse('reports:sales'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'No products yet.')


class CsvExportTests(ReportBase):
    def setUp(self):
        self.client.force_login(self.admin)

    def rows(self, response):
        return list(csv.reader(io.StringIO(response.content.decode())))

    def test_sales_csv(self):
        p = make_product('P-1', 'Phone', price='10.00')
        txn = sell(p, 3, self.staff)
        r = self.client.get(reverse('reports:sales'), {'export': 'sales'})
        self.assertEqual(r['Content-Type'], 'text/csv')
        self.assertIn('sales_report.csv', r['Content-Disposition'])
        rows = self.rows(r)
        self.assertEqual(rows[0], ['Transaction reference', 'Product', 'Quantity sold', 'Sale amount', 'Date', 'Staff member'])
        self.assertEqual(rows[1][0], str(txn.transaction_id))
        self.assertEqual(rows[1][2:4], ['3', '30.00'])
        self.assertEqual(rows[1][5], 'clerk')

    def test_stock_csv(self):
        p = make_product('P-1', 'Phone', price='10.00', qty=20, threshold=8)
        rows = self.rows(self.client.get(reverse('reports:sales'), {'export': 'stock'}))
        self.assertEqual(rows[0][:6], ['Product', 'SKU', 'Category', 'Current stock', 'Reorder threshold', 'Stock value'])
        self.assertEqual(rows[1][:6], ['Phone', 'P-1', 'Phones', '20', '8', '200.00'])

    def test_formula_injection_is_neutralised(self):
        p = make_product('P-1', '=HYPERLINK("http://evil")')
        sell(p, 1, self.staff)
        rows = self.rows(self.client.get(reverse('reports:sales'), {'export': 'sales'}))
        self.assertTrue(rows[1][1].startswith("'="))

    def test_export_respects_date_range(self):
        p = make_product('P-1', 'Phone')
        sell(p, 1, self.staff, days_ago=0)
        sell(p, 1, self.staff, days_ago=90)
        r = self.client.get(reverse('reports:sales'), {'export': 'sales', 'start': '', 'end': ''})
        self.assertEqual(len(self.rows(r)), 3)  # header + both sales (blank dates = all time)
        r = self.client.get(reverse('reports:sales'), {'export': 'sales'})
        self.assertEqual(len(self.rows(r)), 2)  # default last 30 days


class TopSellingTests(ReportBase):
    def setUp(self):
        self.client.force_login(self.admin)

    def test_ranked_by_units_sold(self):
        a = make_product('A', 'Alpha', price='10.00')
        b = make_product('B', 'Beta', price='20.00')
        c = make_product('C', 'Gamma', price='5.00')
        sell(a, 3, self.staff)
        sell(b, 9, self.staff)
        sell(c, 5, self.staff)
        sell(b, 1, self.staff)
        r = self.client.get(reverse('reports:top_selling'))
        self.assertEqual([p.sku for p in r.context['products']], ['B', 'C', 'A'])
        top = r.context['products'][0]
        self.assertEqual((top.units_sold, top.revenue), (10, Decimal('200.00')))

    def test_stock_in_does_not_count(self):
        a = make_product('A', 'Alpha')
        buy(a, 500, self.staff, self.supplier)
        r = self.client.get(reverse('reports:top_selling'))
        self.assertEqual(r.context['products'], [])
        self.assertContains(r, 'No sales recorded for this range.')

    def test_ties_broken_by_name(self):
        b = make_product('B', 'Bravo')
        a = make_product('A', 'Alpha')
        sell(b, 2, self.staff)
        sell(a, 2, self.staff)
        r = self.client.get(reverse('reports:top_selling'))
        self.assertEqual([p.sku for p in r.context['products']], ['A', 'B'])

    def test_only_top_ten(self):
        for i in range(12):
            sell(make_product(f'S{i:02}', f'Item {i:02}'), i + 1, self.staff)
        r = self.client.get(reverse('reports:top_selling'))
        self.assertEqual(len(r.context['products']), 10)
        self.assertEqual(r.context['products'][0].sku, 'S11')

    def test_no_dates_means_all_time_and_dates_filter(self):
        a = make_product('A', 'Alpha')
        b = make_product('B', 'Bravo')
        sell(a, 5, self.staff, days_ago=200)
        sell(b, 1, self.staff, days_ago=1)
        r = self.client.get(reverse('reports:top_selling'))
        self.assertEqual([p.sku for p in r.context['products']], ['A', 'B'])
        start = (timezone.localdate() - timedelta(days=7)).isoformat()
        r = self.client.get(reverse('reports:top_selling'), {'start': start})
        self.assertEqual([p.sku for p in r.context['products']], ['B'])

    def test_bad_range_is_rejected(self):
        r = self.client.get(reverse('reports:top_selling'), {'start': '2026-10-20', 'end': '2026-10-01'})
        self.assertContains(r, 'The start date must be on or before the end date.')
        self.assertNotIn('products', r.context)


class ServiceTests(ReportBase):
    def test_disabled_products_still_appear_in_history(self):
        a = make_product('A', 'Alpha')
        sell(a, 4, self.staff)
        a.status = Product.Status.DISABLED
        a.save()
        self.assertEqual([p.sku for p in services.top_selling(None, None)], ['A'])
