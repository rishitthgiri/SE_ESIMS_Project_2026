from decimal import Decimal

from django.test import TestCase

from catalog.forms import CategoryForm, ProductForm
from catalog.models import Category, Product
from suppliers.models import Supplier


class CatalogFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Laptops')
        self.supplier = Supplier.objects.create(name='Active Supplier')

    def product_data(self, **overrides):
        data = {
            'sku': 'LAP-100',
            'name': 'Laptop',
            'category': str(self.category.pk),
            'price': '25.00',
            'reorder_threshold': '3',
            'supplier': str(self.supplier.pk),
            'status': Product.Status.ACTIVE,
        }
        data.update(overrides)
        return data

    def test_category_form_trims_name_and_rejects_case_insensitive_duplicate(self):
        form = CategoryForm(data={'name': '  Audio  ', 'status': Category.Status.ACTIVE})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['name'], 'Audio')

        duplicate = CategoryForm(data={'name': '  laptops ', 'status': Category.Status.ACTIVE})
        self.assertFalse(duplicate.is_valid())
        self.assertIn('name', duplicate.errors)

    def test_product_form_trims_values_and_rejects_case_insensitive_duplicate_sku(self):
        form = ProductForm(data=self.product_data(sku='  LAP-100  ', name='  Work laptop  '))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['sku'], 'LAP-100')
        self.assertEqual(form.cleaned_data['name'], 'Work laptop')

        Product.objects.create(
            sku='PHONE-001', name='Phone', category=self.category,
            price=Decimal('20.00'),
        )
        duplicate = ProductForm(data=self.product_data(sku='phone-001'))
        self.assertFalse(duplicate.is_valid())
        self.assertIn('sku', duplicate.errors)

    def test_disabled_category_and_supplier_are_not_valid_add_choices(self):
        disabled_category = Category.objects.create(
            name='Old Category', status=Category.Status.DISABLED,
        )
        disabled_supplier = Supplier.objects.create(
            name='Old Supplier', status=Supplier.Status.DISABLED,
        )
        form = ProductForm(data=self.product_data(
            category=str(disabled_category.pk), supplier=str(disabled_supplier.pk),
        ))

        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)
        self.assertIn('supplier', form.errors)
        self.assertNotIn(disabled_category, form.fields['category'].queryset)
        self.assertNotIn(disabled_supplier, form.fields['supplier'].queryset)

    def test_edit_keeps_its_own_disabled_category_available(self):
        self.category.status = Category.Status.DISABLED
        self.category.save(update_fields=['status'])
        product = Product.objects.create(
            sku='LAP-200', name='Existing Laptop', category=self.category,
            price=Decimal('40.00'),
        )

        form = ProductForm(data=self.product_data(sku='LAP-200'), instance=product)

        self.assertIn(self.category, form.fields['category'].queryset)
        self.assertTrue(form.is_valid(), form.errors)
