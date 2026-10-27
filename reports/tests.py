from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from transactions import services
from suppliers.models import Supplier

from .alerts import is_low_stock, low_stock_products

User = get_user_model()


class LowStockRuleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='Cables')

    def make(self, sku, qty, threshold, status='active'):
        return Product.objects.create(
            sku=sku, name=sku, category=self.cat, price='1.00',
            quantity_in_stock=qty, reorder_threshold=threshold, status=status,
        )

    def test_strictly_below_threshold_is_low(self):
        self.assertTrue(is_low_stock(self.make('A', 4, 5)))

    def test_equal_to_threshold_is_not_low(self):
        self.assertFalse(is_low_stock(self.make('B', 5, 5)))

    def test_above_threshold_is_not_low(self):
        self.assertFalse(is_low_stock(self.make('C', 9, 5)))

    def test_zero_threshold_never_low(self):
        self.assertFalse(is_low_stock(self.make('D', 0, 0)))

    def test_queryset_matches_rule_and_skips_disabled(self):
        low = self.make('LOW', 1, 5)
        self.make('OK', 5, 5)
        self.make('OFF', 0, 5, status='disabled')
        self.assertEqual(list(low_stock_products()), [low])

    def test_most_urgent_first(self):
        a = self.make('A', 3, 5)
        b = self.make('B', 0, 5)
        self.assertEqual(list(low_stock_products()), [b, a])


class LowStockViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user('boss', 'boss@x.com', 'pw12345!', role=User.Role.ADMIN)
        cls.staff = User.objects.create_user('clerk', 'clerk@x.com', 'pw12345!', role=User.Role.STAFF)
        cat = Category.objects.create(name='Cables')
        cls.product = Product.objects.create(
            sku='USB', name='USB Cable', category=cat, price='5.00',
            quantity_in_stock=10, reorder_threshold=5,
        )

    def test_anonymous_redirected(self):
        self.assertEqual(self.client.get(reverse('reports:low_stock')).status_code, 302)

    def test_staff_and_admin_can_view_report_and_dashboard(self):
        services.record_stock_out(product=self.product, quantity=6, user=self.staff)  # 10 -> 4 < 5
        for user in (self.staff, self.admin):
            self.client.force_login(user)
            self.assertContains(self.client.get(reverse('reports:low_stock')), 'USB Cable')
            self.assertContains(self.client.get(reverse('accounts:dashboard')), 'USB Cable')

    def test_alert_clears_after_restock(self):
        sup = Supplier.objects.create(name='S')
        services.record_stock_out(product=self.product, quantity=6, user=self.staff)
        self.assertEqual(low_stock_products().count(), 1)
        services.record_stock_in(product=self.product, supplier=sup, quantity=5, user=self.staff)  # 4 -> 9
        self.assertEqual(low_stock_products().count(), 0)
        self.client.force_login(self.admin)
        self.assertNotContains(self.client.get(reverse('accounts:dashboard')), 'USB Cable')

    def test_empty_state_message(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse('reports:low_stock')), 'above their reorder level')
