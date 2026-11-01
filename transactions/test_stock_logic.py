"""ESIMS-25: stock calculation and low-stock threshold logic, tested WITHOUT the UI (NFR-006).

The first class needs no database and no HTTP at all.
Run: python manage.py test transactions.test_stock_logic -v 2
"""
import inspect
import random

from django.test import SimpleTestCase

from catalog.models import Product
from reports.alerts import is_low_stock, low_stock_products

from . import services, views
from .models import StockTransaction
from .testutils import StockTestBase


class PureCalculationTests(SimpleTestCase):
    """UT-STOCK-01/02: arithmetic and rules with plain numbers."""

    def test_stock_after_in(self):
        self.assertEqual(services.stock_after_in(0, 1), 1)
        self.assertEqual(services.stock_after_in(5, 10), 15)
        self.assertEqual(services.stock_after_in(5, services.MAX_QUANTITY), 5 + services.MAX_QUANTITY)

    def test_stock_after_out(self):
        self.assertEqual(services.stock_after_out(5, 1), 4)
        self.assertEqual(services.stock_after_out(5, 3), 2)

    def test_selling_exactly_everything_is_allowed_one_more_is_not(self):
        self.assertEqual(services.stock_after_out(5, 5), 0)
        with self.assertRaises(services.InsufficientStock):
            services.stock_after_out(5, 6)
        with self.assertRaises(services.InsufficientStock):
            services.stock_after_out(0, 1)

    def test_over_sale_message_names_the_stock_and_the_product(self):
        with self.assertRaisesMessage(services.InsufficientStock, 'Only 5 unit(s) of MOB-001 in stock; cannot sell 6.'):
            services.stock_after_out(5, 6, label='MOB-001')

    def test_bad_quantities_are_rejected_by_both_calculations(self):
        for calc in (services.stock_after_in, services.stock_after_out):
            for bad in (0, -1, 1.5, '3', None, True, services.MAX_QUANTITY + 1):
                with self.subTest(calc=calc.__name__, quantity=bad):
                    with self.assertRaises(services.InvalidStockOperation):
                        calc(10, bad)

    def test_calculations_never_change_their_inputs_or_go_negative(self):
        rng = random.Random(7)
        for _ in range(500):
            current, qty = rng.randint(0, 50), rng.randint(1, 60)
            try:
                result = services.stock_after_out(current, qty)
            except services.InsufficientStock:
                self.assertGreater(qty, current)
            else:
                self.assertGreaterEqual(result, 0)
                self.assertEqual(result, current - qty)


class ThresholdTests(StockTestBase):
    """UT-ALERT-01 / FR-017: the low-stock rule (strictly below the reorder threshold)."""

    def refreshed(self):
        return Product.objects.get(pk=self.product.pk)    # stock 5, threshold 2

    def test_boundary_values(self):
        for stock, threshold, expected in ((5, 2, False), (2, 2, False), (1, 2, True), (0, 2, True), (0, 0, False)):
            with self.subTest(stock=stock, threshold=threshold):
                p = Product(quantity_in_stock=stock, reorder_threshold=threshold)
                self.assertEqual(is_low_stock(p), expected)

    def test_stock_out_that_crosses_the_threshold_raises_the_alert(self):
        services.record_stock_out(product=self.product, quantity=3, user=self.staff)       # 5 -> 2
        self.assertFalse(is_low_stock(self.refreshed()))                                   # equal is NOT low
        self.assertNotIn(self.product, low_stock_products())
        services.record_stock_out(product=self.product, quantity=1, user=self.staff)       # 2 -> 1
        self.assertTrue(is_low_stock(self.refreshed()))
        self.assertIn(self.product, low_stock_products())

    def test_stock_in_clears_the_alert(self):
        services.record_stock_out(product=self.product, quantity=4, user=self.staff)       # 5 -> 1 (low)
        self.assertIn(self.product, low_stock_products())
        services.record_stock_in(product=self.product, supplier=self.supplier, quantity=10, user=self.staff)
        self.assertNotIn(self.product, low_stock_products())

    def test_a_rejected_sale_does_not_change_the_alert_state(self):
        with self.assertRaises(services.InsufficientStock):
            services.record_stock_out(product=self.product, quantity=6, user=self.staff)
        self.assertFalse(is_low_stock(self.refreshed()))

    def test_disabled_products_are_not_listed_as_low_stock(self):
        self.product.quantity_in_stock = 0
        self.product.status = Product.Status.DISABLED
        self.product.save()
        self.assertNotIn(self.product, low_stock_products())


class LedgerConsistencyTests(StockTestBase):
    """Stock must always equal: starting stock + all stock-ins - all stock-outs."""

    def test_long_random_sequence_keeps_stock_equal_to_history(self):
        rng = random.Random(2026)
        start = self.stock()
        for _ in range(60):
            qty = rng.randint(1, 8)
            if rng.random() < 0.5:
                services.record_stock_in(product=self.product, supplier=self.supplier, quantity=qty, user=self.staff)
            else:
                try:
                    services.record_stock_out(product=self.product, quantity=qty, user=self.staff)
                except services.InsufficientStock:
                    pass
            self.assertGreaterEqual(self.stock(), 0)
        ins = sum(t.quantity for t in StockTransaction.objects.filter(transaction_type='IN'))
        outs = sum(t.quantity for t in StockTransaction.objects.filter(transaction_type='OUT'))
        self.assertEqual(self.stock(), start + ins - outs)

    def test_known_sequence(self):
        for op, qty in (('in', 5), ('out', 12), ('in', 1), ('out', 4)):      # 5 -> 10 -> -2? no: 10, then 12 > 10
            try:
                if op == 'in':
                    services.record_stock_in(product=self.product, supplier=self.supplier, quantity=qty, user=self.staff)
                else:
                    services.record_stock_out(product=self.product, quantity=qty, user=self.staff)
            except services.InsufficientStock:
                pass
        # 5 +5 = 10; sell 12 rejected; +1 = 11; -4 = 7
        self.assertEqual(self.stock(), 7)
        self.assertEqual(StockTransaction.objects.count(), 3)


class SeparationFromUITests(SimpleTestCase):
    """Acceptance criterion: stock calculation logic is separated from the views."""

    def test_views_do_no_stock_arithmetic(self):
        source = inspect.getsource(views)
        # Views may READ the new stock level to show a message, but never change it.
        self.assertNotRegex(source, r'quantity_in_stock\s*[-+*/]?=[^=]')
        self.assertNotIn('select_for_update', source)
        self.assertNotIn('.save(', source)
        self.assertNotIn('F(', source)

    def test_services_know_nothing_about_http(self):
        source = inspect.getsource(services)
        for forbidden in ('django.http', 'django.shortcuts', 'HttpRequest', 'messages'):
            self.assertNotIn(forbidden, source)
        for fn in (services.record_stock_in, services.record_stock_out,
                   services.stock_after_in, services.stock_after_out):
            self.assertNotIn('request', inspect.signature(fn).parameters)
