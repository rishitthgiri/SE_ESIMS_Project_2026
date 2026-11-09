"""Phase 3 additions for UT-ALERT-01 / ST-ALERT-01 (FR-017) and ST-REPORT-01 (FR-018)."""
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

from .alerts import is_low_stock, low_stock_products


class LowStockFlowTests(TestCase):
    """ST-ALERT-01: reduce the quantity step by step and watch the alert appear and clear."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = make_admin('boss')
        cls.staff = make_user('clerk')
        cls.supplier = Supplier.objects.create(name='Acme')
        cat = Category.objects.create(name='Phones')
        cls.product = Product.objects.create(
            sku='P-1', name='Phone', category=cat, price='100.00', quantity_in_stock=8, reorder_threshold=5)

    def test_alert_appears_only_when_strictly_below_threshold(self):
        stock.record_stock_out(product=self.product, quantity=3, user=self.staff)   # 8 -> 5 (equal)
        self.product.refresh_from_db()
        self.assertFalse(is_low_stock(self.product))
        self.assertEqual(low_stock_products().count(), 0)
        stock.record_stock_out(product=self.product, quantity=1, user=self.staff)   # 5 -> 4 (below)
        self.product.refresh_from_db()
        self.assertTrue(is_low_stock(self.product))
        self.assertEqual([p.sku for p in low_stock_products()], ['P-1'])

    def test_both_roles_see_the_alert_on_page_and_dashboard(self):
        stock.record_stock_out(product=self.product, quantity=6, user=self.staff)   # 8 -> 2
        for user in (self.staff, self.admin):
            self.client.force_login(user)
            self.assertContains(self.client.get(reverse('reports:low_stock')), 'Phone')
            self.assertContains(self.client.get(reverse('accounts:dashboard')), 'Phone')

    def test_disabling_the_product_removes_the_alert(self):
        stock.record_stock_out(product=self.product, quantity=6, user=self.staff)
        self.assertEqual(low_stock_products().count(), 1)
        self.product.status = Product.Status.DISABLED
        self.product.save()
        self.assertEqual(low_stock_products().count(), 0)

    def test_restock_clears_the_alert(self):
        stock.record_stock_out(product=self.product, quantity=6, user=self.staff)   # 2
        stock.record_stock_in(product=self.product, supplier=self.supplier, quantity=3, user=self.staff)  # 5 (equal)
        self.assertEqual(low_stock_products().count(), 0)


class ReportAmountRuleTests(TestCase):
    """Documented deviation 8: sale amount uses the CURRENT price (no price snapshot on transactions)."""

    def test_price_change_changes_old_sale_amounts(self):
        admin, staff = make_admin('boss'), make_user('clerk')
        cat = Category.objects.create(name='Phones')
        product = Product.objects.create(
            sku='P-1', name='Phone', category=cat, price='10.00', quantity_in_stock=20, reorder_threshold=1)
        txn = stock.record_stock_out(product=product, quantity=2, user=staff)
        StockTransaction.objects.filter(pk=txn.pk).update(timestamp=timezone.now() - timedelta(days=1))
        self.client.force_login(admin)
        before = self.client.get(reverse('reports:sales')).context['totals']['amount']
        self.assertEqual(before, Decimal('20.00'))
        Product.objects.filter(pk=product.pk).update(price='15.00')
        after = self.client.get(reverse('reports:sales')).context['totals']['amount']
        self.assertEqual(after, Decimal('30.00'))
