from decimal import Decimal

from django.test import TestCase

from catalog.models import Category, Product
from catalog.selectors import search_products


class SearchProductsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Laptops')
        self.other_category = Category.objects.create(name='Phones')
        self.laptop = Product.objects.create(
            sku='LAP-001', name='Gaming Laptop', category=self.category,
            price=Decimal('100.00'),
        )
        self.disabled_laptop = Product.objects.create(
            sku='LAP-002', name='Office Laptop', category=self.category,
            price=Decimal('80.00'), status=Product.Status.DISABLED,
        )
        self.phone = Product.objects.create(
            sku='PHN-GAME', name='Gaming Phone', category=self.other_category,
            price=Decimal('60.00'),
        )

    def test_search_matches_name_or_sku_case_insensitively(self):
        self.assertEqual(
            set(search_products(q='gaming').values_list('pk', flat=True)),
            {self.laptop.pk, self.phone.pk},
        )
        self.assertEqual(
            list(search_products(q='phn-gam').values_list('pk', flat=True)),
            [self.phone.pk],
        )

    def test_category_filter(self):
        self.assertEqual(
            set(search_products(category=str(self.category.pk)).values_list('pk', flat=True)),
            {self.laptop.pk, self.disabled_laptop.pk},
        )

    def test_status_filter(self):
        self.assertEqual(
            list(search_products(status=Product.Status.DISABLED).values_list('pk', flat=True)),
            [self.disabled_laptop.pk],
        )

    def test_combined_filters(self):
        self.assertEqual(
            list(search_products(
                q='gaming', category=str(self.category.pk), status=Product.Status.ACTIVE,
            ).values_list('pk', flat=True)),
            [self.laptop.pk],
        )

    def test_invalid_category_uuid_is_ignored(self):
        self.assertEqual(search_products(category='not-a-uuid').count(), 3)
