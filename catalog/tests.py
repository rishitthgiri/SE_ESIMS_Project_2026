from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from suppliers.models import Supplier
from .models import Category, Product

User = get_user_model()
PASSWORD = 'Pass@12345'


class CategoryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin1', 'admin1@esims.local', PASSWORD, role='ADMIN')
        self.staff = User.objects.create_user(
            'staff1', 'staff1@esims.local', PASSWORD, role='STAFF')

    def test_admin_can_add_category(self):
        self.client.login(username='admin1', password=PASSWORD)
        r = self.client.post(reverse('catalog:category_add'),
                             {'name': 'Mobiles', 'status': 'active'})
        self.assertRedirects(r, reverse('catalog:category_list'))
        self.assertTrue(Category.objects.filter(name='Mobiles').exists())

    def test_duplicate_name_rejected(self):
        Category.objects.create(name='Mobiles')
        self.client.login(username='admin1', password=PASSWORD)
        self.client.post(reverse('catalog:category_add'),
                         {'name': 'mobiles', 'status': 'active'})
        self.assertEqual(Category.objects.count(), 1)

    def test_blank_name_rejected(self):
        self.client.login(username='admin1', password=PASSWORD)
        self.client.post(reverse('catalog:category_add'),
                         {'name': '  ', 'status': 'active'})
        self.assertEqual(Category.objects.count(), 0)

    def test_edit_can_disable(self):
        c = Category.objects.create(name='Audio')
        self.client.login(username='admin1', password=PASSWORD)
        self.client.post(reverse('catalog:category_edit', args=[c.pk]),
                         {'name': 'Audio', 'status': 'disabled'})
        c.refresh_from_db()
        self.assertEqual(c.status, 'disabled')

    def test_staff_blocked(self):
        self.client.login(username='staff1', password=PASSWORD)
        r = self.client.post(reverse('catalog:category_add'),
                             {'name': 'Mobiles', 'status': 'active'})
        self.assertIn(r.status_code, (302, 403))
        self.assertEqual(Category.objects.count(), 0)

    def test_anonymous_redirected_to_login(self):
        r = self.client.get(reverse('catalog:category_list'))
        self.assertEqual(r.status_code, 302)


class ProductAddTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin1', 'admin1@esims.local', PASSWORD, role='ADMIN'
        )
        self.staff = User.objects.create_user(
            'staff1', 'staff1@esims.local', PASSWORD, role='STAFF'
        )
        self.category = Category.objects.create(name='Laptops', status=Category.Status.ACTIVE)
        self.supplier = Supplier.objects.create(name='TechCorp', status=Supplier.Status.ACTIVE)

    def test_admin_can_add_product(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'LAP-001',
            'name': 'ThinkPad X1',
            'category': self.category.pk,
            'price': '1299.99',
            'reorder_threshold': 5,
            'supplier': self.supplier.pk,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertRedirects(response, reverse('catalog:product_list'))
        product = Product.objects.get(sku='LAP-001')
        self.assertEqual(product.name, 'ThinkPad X1')
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.price, Decimal('1299.99'))
        self.assertEqual(product.reorder_threshold, 5)
        self.assertEqual(product.supplier, self.supplier)
        self.assertEqual(product.quantity_in_stock, 0)
        self.assertEqual(product.status, 'active')

    def test_stock_cannot_be_set_via_post(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'LAP-002',
            'name': 'MacBook Pro',
            'category': self.category.pk,
            'price': '1999.99',
            'reorder_threshold': 3,
            'status': 'active',
            'quantity_in_stock': 150,
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertRedirects(response, reverse('catalog:product_list'))
        product = Product.objects.get(sku='LAP-002')
        self.assertEqual(product.quantity_in_stock, 0)

    def test_duplicate_sku_any_case_rejected(self):
        Product.objects.create(
            sku='SKU-100',
            name='Existing Item',
            category=self.category,
            price=Decimal('50.00'),
            reorder_threshold=5,
        )
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'sku-100',
            'name': 'Different Item',
            'category': self.category.pk,
            'price': '75.00',
            'reorder_threshold': 5,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'sku', 'A product with this SKU already exists.')
        self.assertEqual(Product.objects.filter(sku__iexact='sku-100').count(), 1)

    def test_negative_price_rejected(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'NEG-001',
            'name': 'Negative Price Item',
            'category': self.category.pk,
            'price': '-10.00',
            'reorder_threshold': 5,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('price'))
        self.assertFalse(Product.objects.filter(sku='NEG-001').exists())

    def test_negative_reorder_threshold_rejected(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'NEG-002',
            'name': 'Negative Threshold Item',
            'category': self.category.pk,
            'price': '10.00',
            'reorder_threshold': -1,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('reorder_threshold'))
        self.assertFalse(Product.objects.filter(sku='NEG-002').exists())

    def test_required_fields(self):
        self.client.login(username='admin1', password=PASSWORD)
        response = self.client.post(reverse('catalog:product_add'), {})
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors.get('sku'))
        self.assertTrue(form.errors.get('name'))
        self.assertTrue(form.errors.get('category'))
        self.assertTrue(form.errors.get('price'))
        self.assertEqual(Product.objects.count(), 0)

    def test_blank_or_whitespace_name_rejected(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'WHT-001',
            'name': '   ',
            'category': self.category.pk,
            'price': '10.00',
            'reorder_threshold': 5,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('name'))
        self.assertEqual(Product.objects.count(), 0)

    def test_blank_or_whitespace_sku_rejected(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': '   ',
            'name': 'Valid Name',
            'category': self.category.pk,
            'price': '10.00',
            'reorder_threshold': 5,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('sku'))
        self.assertEqual(Product.objects.count(), 0)

    def test_disabled_category_not_accepted(self):
        disabled_cat = Category.objects.create(name='Old Category', status=Category.Status.DISABLED)
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'DIS-001',
            'name': 'Item with Disabled Cat',
            'category': disabled_cat.pk,
            'price': '25.00',
            'reorder_threshold': 5,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('category'))
        self.assertFalse(Product.objects.filter(sku='DIS-001').exists())

    def test_disabled_supplier_not_accepted(self):
        disabled_sup = Supplier.objects.create(name='Old Supplier', status=Supplier.Status.DISABLED)
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'DIS-002',
            'name': 'Item with Disabled Sup',
            'category': self.category.pk,
            'price': '25.00',
            'reorder_threshold': 5,
            'supplier': disabled_sup.pk,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('supplier'))
        self.assertFalse(Product.objects.filter(sku='DIS-002').exists())

    def test_supplier_optional(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'NOSUP-001',
            'name': 'No Supplier Item',
            'category': self.category.pk,
            'price': '15.00',
            'reorder_threshold': 0,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertRedirects(response, reverse('catalog:product_list'))
        product = Product.objects.get(sku='NOSUP-001')
        self.assertIsNone(product.supplier)

    def test_sku_and_name_trimmed(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': '  TRIM-001  ',
            'name': '  Trimmed Name  ',
            'category': self.category.pk,
            'price': '15.00',
            'reorder_threshold': 0,
            'status': 'active',
        }
        response = self.client.post(reverse('catalog:product_add'), data)
        self.assertRedirects(response, reverse('catalog:product_list'))
        product = Product.objects.get(sku='TRIM-001')
        self.assertEqual(product.sku, 'TRIM-001')
        self.assertEqual(product.name, 'Trimmed Name')

    def test_staff_cannot_add_product(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.post(reverse('catalog:product_add'), {
            'sku': 'STF-001',
            'name': 'Staff Attempt',
            'category': self.category.pk,
            'price': '10.00',
            'reorder_threshold': 1,
            'status': 'active',
        })
        self.assertIn(response.status_code, (302, 403))
        self.assertEqual(Product.objects.count(), 0)

    def test_staff_can_view_product_list(self):
        Product.objects.create(
            sku='VIEW-001',
            name='Visible Item',
            category=self.category,
            price=Decimal('10.00'),
            quantity_in_stock=42,
        )
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VIEW-001')
        self.assertContains(response, 'Visible Item')
        self.assertContains(response, '42')

    def test_anonymous_redirected_to_login(self):
        r_list = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(r_list.status_code, 302)

        r_add = self.client.get(reverse('catalog:product_add'))
        self.assertEqual(r_add.status_code, 302)

    def test_admin_sees_add_button_staff_does_not(self):
        self.client.login(username='admin1', password=PASSWORD)
        r_admin = self.client.get(reverse('catalog:product_list'))
        self.assertContains(r_admin, reverse('catalog:product_add'))

        self.client.login(username='staff1', password=PASSWORD)
        r_staff = self.client.get(reverse('catalog:product_list'))
        self.assertNotContains(r_staff, reverse('catalog:product_add'))
