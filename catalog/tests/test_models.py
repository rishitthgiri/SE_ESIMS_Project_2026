from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Category, Product


class CatalogModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Laptops')

    def make_product(self, **overrides):
        values = {
            'sku': 'LAP-001',
            'name': 'Laptop',
            'category': self.category,
            'price': Decimal('10.00'),
        }
        values.update(overrides)
        return Product(**values)

    def test_model_string_values_and_product_active_property(self):
        product = self.make_product()
        self.assertEqual(str(self.category), 'Laptops')
        self.assertEqual(str(product), 'LAP-001 - Laptop')
        self.assertTrue(product.is_active)
        product.status = Product.Status.DISABLED
        self.assertFalse(product.is_active)

    def test_negative_price_is_rejected_by_full_clean(self):
        product = self.make_product(price=Decimal('-0.01'))
        with self.assertRaises(ValidationError) as error:
            product.full_clean()
        self.assertIn('price', error.exception.message_dict)

    def test_sku_and_category_name_must_be_unique(self):
        self.make_product().save()
        duplicate_sku = self.make_product(name='Another laptop')
        with self.assertRaises(ValidationError) as sku_error:
            duplicate_sku.full_clean()
        self.assertIn('sku', sku_error.exception.message_dict)

        duplicate_category = Category(name='Laptops')
        with self.assertRaises(ValidationError) as category_error:
            duplicate_category.full_clean()
        self.assertIn('name', category_error.exception.message_dict)

    def test_positive_integer_fields_reject_negative_values(self):
        for field_name in ('quantity_in_stock', 'reorder_threshold'):
            product = self.make_product(**{field_name: -1})
            with self.subTest(field=field_name):
                with self.assertRaises(ValidationError) as error:
                    product.full_clean()
                self.assertIn(field_name, error.exception.message_dict)
