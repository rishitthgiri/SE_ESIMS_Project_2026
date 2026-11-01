from decimal import Decimal
import time
import uuid

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from catalog.models import Category, Product
from suppliers.models import Supplier
from transactions.forms import StockOutForm
from transactions.models import StockTransaction

User = get_user_model()
PASSWORD = 'Pass@12345'

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

class ProductEditTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin1', 'admin1@esims.local', PASSWORD, role='ADMIN'
        )
        self.staff = User.objects.create_user(
            'staff1', 'staff1@esims.local', PASSWORD, role='STAFF'
        )
        self.category = Category.objects.create(name='Laptops', status=Category.Status.ACTIVE)
        self.supplier = Supplier.objects.create(name='TechCorp', status=Supplier.Status.ACTIVE)
        self.product = Product.objects.create(
            sku='LAP-001',
            name='ThinkPad X1',
            category=self.category,
            price=Decimal('1200.00'),
            reorder_threshold=5,
            quantity_in_stock=10,
            supplier=self.supplier,
            status=Product.Status.ACTIVE,
        )

    def test_admin_can_edit_name_and_price(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'LAP-001',
            'name': 'ThinkPad X1 Carbon Gen 10',
            'category': self.category.pk,
            'price': '1399.50',
            'reorder_threshold': 5,
            'supplier': self.supplier.pk,
            'status': 'active',
        }
        response = self.client.post(
            reverse('catalog:product_edit', args=[self.product.pk]), data
        )
        self.assertRedirects(response, reverse('catalog:product_list'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'ThinkPad X1 Carbon Gen 10')
        self.assertEqual(self.product.price, Decimal('1399.50'))

    def test_sku_clash_with_another_product_rejected(self):
        Product.objects.create(
            sku='LAP-002',
            name='Dell XPS 13',
            category=self.category,
            price=Decimal('1100.00'),
            reorder_threshold=3,
        )
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'lap-002',
            'name': 'ThinkPad X1',
            'category': self.category.pk,
            'price': '1200.00',
            'reorder_threshold': 5,
            'status': 'active',
        }
        response = self.client.post(
            reverse('catalog:product_edit', args=[self.product.pk]), data
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'], 'sku', 'A product with this SKU already exists.'
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.sku, 'LAP-001')

    def test_keeping_its_own_sku_allowed(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'lap-001',
            'name': 'ThinkPad Updated',
            'category': self.category.pk,
            'price': '1200.00',
            'reorder_threshold': 5,
            'status': 'active',
        }
        response = self.client.post(
            reverse('catalog:product_edit', args=[self.product.pk]), data
        )
        self.assertRedirects(response, reverse('catalog:product_list'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'ThinkPad Updated')
        self.assertEqual(self.product.sku, 'lap-001')

    def test_stock_unchanged_even_if_posted(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'LAP-001',
            'name': 'ThinkPad X1',
            'category': self.category.pk,
            'price': '1200.00',
            'reorder_threshold': 5,
            'status': 'active',
            'quantity_in_stock': 999,
        }
        response = self.client.post(
            reverse('catalog:product_edit', args=[self.product.pk]), data
        )
        self.assertRedirects(response, reverse('catalog:product_list'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 10)

    def test_edit_can_disable_product(self):
        self.client.login(username='admin1', password=PASSWORD)
        data = {
            'sku': 'LAP-001',
            'name': 'ThinkPad X1',
            'category': self.category.pk,
            'price': '1200.00',
            'reorder_threshold': 5,
            'status': 'disabled',
        }
        response = self.client.post(
            reverse('catalog:product_edit', args=[self.product.pk]), data
        )
        self.assertRedirects(response, reverse('catalog:product_list'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'disabled')
        self.assertEqual(self.product.quantity_in_stock, 10)

    def test_editing_works_when_current_category_is_disabled(self):
        self.category.status = Category.Status.DISABLED
        self.category.save()

        self.client.login(username='admin1', password=PASSWORD)
        r_get = self.client.get(reverse('catalog:product_edit', args=[self.product.pk]))
        self.assertEqual(r_get.status_code, 200)

        data = {
            'sku': 'LAP-001',
            'name': 'ThinkPad Renamed',
            'category': self.category.pk,
            'price': '1200.00',
            'reorder_threshold': 5,
            'status': 'active',
        }
        response = self.client.post(
            reverse('catalog:product_edit', args=[self.product.pk]), data
        )
        self.assertRedirects(response, reverse('catalog:product_list'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'ThinkPad Renamed')
        self.assertEqual(self.product.category, self.category)

    def test_editing_works_when_current_supplier_is_disabled(self):
        self.supplier.status = Supplier.Status.DISABLED
        self.supplier.save()

        self.client.login(username='admin1', password=PASSWORD)
        r_get = self.client.get(reverse('catalog:product_edit', args=[self.product.pk]))
        self.assertEqual(r_get.status_code, 200)

        data = {
            'sku': 'LAP-001',
            'name': 'ThinkPad Supplier Test',
            'category': self.category.pk,
            'price': '1200.00',
            'reorder_threshold': 5,
            'supplier': self.supplier.pk,
            'status': 'active',
        }
        response = self.client.post(
            reverse('catalog:product_edit', args=[self.product.pk]), data
        )
        self.assertRedirects(response, reverse('catalog:product_list'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.supplier, self.supplier)

    def test_unknown_pk_returns_404(self):
        self.client.login(username='admin1', password=PASSWORD)
        unknown_pk = uuid.uuid4()
        response = self.client.get(reverse('catalog:product_edit', args=[unknown_pk]))
        self.assertEqual(response.status_code, 404)

    def test_staff_cannot_edit_product(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.post(
            reverse('catalog:product_edit', args=[self.product.pk]),
            {
                'sku': 'LAP-001',
                'name': 'Hacked by staff',
                'category': self.category.pk,
                'price': '1.00',
                'reorder_threshold': 0,
                'status': 'active',
            },
        )
        self.assertIn(response.status_code, (302, 403))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'ThinkPad X1')

    def test_admin_sees_edit_link_staff_does_not(self):
        edit_url = reverse('catalog:product_edit', args=[self.product.pk])

        self.client.login(username='admin1', password=PASSWORD)
        r_admin = self.client.get(reverse('catalog:product_list'))
        self.assertContains(r_admin, edit_url)

        self.client.login(username='staff1', password=PASSWORD)
        r_staff = self.client.get(reverse('catalog:product_list'))
        self.assertNotContains(r_staff, edit_url)

    def test_anonymous_redirected_to_login(self):
        edit_url = reverse('catalog:product_edit', args=[self.product.pk])
        r = self.client.get(edit_url)
        self.assertEqual(r.status_code, 302)

class ProductDisableTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin1', 'admin1@esims.local', PASSWORD, role='ADMIN'
        )
        self.staff = User.objects.create_user(
            'staff1', 'staff1@esims.local', PASSWORD, role='STAFF'
        )
        self.category = Category.objects.create(name='Laptops')
        self.product = Product.objects.create(
            sku='LAP-DIS-001', name='Disable Test Laptop', category=self.category,
            price=Decimal('1200.00'), quantity_in_stock=10,
        )
        self.url = reverse('catalog:product_disable', args=[self.product.pk])

    def test_admin_post_disables_product_without_changing_stock(self):
        self.client.force_login(self.admin)

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('catalog:product_list'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.Status.DISABLED)
        self.assertEqual(self.product.quantity_in_stock, 10)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_get_shows_confirmation_without_disabling(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.Status.ACTIVE)

    def test_product_list_only_offers_disable_for_active_products(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('catalog:product_list'))
        self.assertContains(response, self.url)

        self.product.status = Product.Status.DISABLED
        self.product.save(update_fields=['status'])
        response = self.client.get(reverse('catalog:product_list'))
        self.assertContains(response, 'Disabled')
        self.assertNotContains(response, self.url)

    def test_staff_is_blocked_and_anonymous_user_is_redirected(self):
        self.client.force_login(self.staff)
        self.assertIn(self.client.post(self.url).status_code, (302, 403))
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.Status.ACTIVE)

        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_disabling_preserves_stock_transaction_history(self):
        transaction = StockTransaction.objects.create(
            product=self.product, user=self.admin,
            transaction_type=StockTransaction.Type.OUT, quantity=1,
        )
        self.client.force_login(self.admin)

        self.client.post(self.url)

        self.assertTrue(StockTransaction.objects.filter(pk=transaction.pk).exists())
        self.assertEqual(StockOutForm().fields['product'].queryset.filter(
            pk=self.product.pk
        ).count(), 0)

    def test_already_disabled_product_gets_harmless_message(self):
        self.product.status = Product.Status.DISABLED
        self.product.save(update_fields=['status'])
        self.client.force_login(self.admin)

        response = self.client.post(self.url, follow=True)

        self.assertContains(response, 'Product is already disabled.')

    def test_unknown_product_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('catalog:product_disable', args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)

class ProductSearchFilterTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin1', 'admin1@esims.local', PASSWORD, role='ADMIN'
        )
        self.staff = User.objects.create_user(
            'staff1', 'staff1@esims.local', PASSWORD, role='STAFF'
        )
        self.cat_laptops = Category.objects.create(name='Laptops', status=Category.Status.ACTIVE)
        self.cat_phones = Category.objects.create(name='Phones', status=Category.Status.ACTIVE)
        self.cat_audio = Category.objects.create(name='Audio', status=Category.Status.DISABLED)

        self.p1 = Product.objects.create(
            sku='LAP-X1',
            name='ThinkPad X1',
            category=self.cat_laptops,
            price=Decimal('1200.00'),
            quantity_in_stock=10,
            status=Product.Status.ACTIVE,
        )
        self.p2 = Product.objects.create(
            sku='LAP-XPS',
            name='Dell XPS 15',
            category=self.cat_laptops,
            price=Decimal('1500.00'),
            quantity_in_stock=5,
            status=Product.Status.DISABLED,
        )
        self.p3 = Product.objects.create(
            sku='PHN-IP14',
            name='iPhone 14 Pro',
            category=self.cat_phones,
            price=Decimal('999.00'),
            quantity_in_stock=20,
            status=Product.Status.ACTIVE,
        )

    def test_search_by_name_partial_case_insensitive(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(reverse('catalog:product_list'), {'q': 'thinkpad'})
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertIn(self.p1, products)
        self.assertNotIn(self.p2, products)
        self.assertNotIn(self.p3, products)

    def test_search_by_sku_partial_case_insensitive(self):
        self.client.login(username='admin1', password=PASSWORD)
        response = self.client.get(reverse('catalog:product_list'), {'q': 'lap'})
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(len(products), 2)
        self.assertIn(self.p1, products)
        self.assertIn(self.p2, products)
        self.assertNotIn(self.p3, products)

    def test_filter_by_category(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(
            reverse('catalog:product_list'), {'category': str(self.cat_phones.pk)}
        )
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(products, [self.p3])

    def test_filter_by_status(self):
        self.client.login(username='admin1', password=PASSWORD)
        response = self.client.get(reverse('catalog:product_list'), {'status': 'disabled'})
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(products, [self.p2])

    def test_combined_filters(self):
        self.client.login(username='admin1', password=PASSWORD)
        response = self.client.get(
            reverse('catalog:product_list'),
            {
                'q': 'X1',
                'category': str(self.cat_laptops.pk),
                'status': 'active',
            },
        )
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'])
        self.assertEqual(products, [self.p1])

    def test_combined_filters_no_match(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(
            reverse('catalog:product_list'),
            {
                'q': 'iPhone',
                'category': str(self.cat_laptops.pk),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)
        self.assertContains(response, 'No products match your search.')

    def test_invalid_category_uuid_does_not_crash(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(reverse('catalog:product_list'), {'category': 'not-a-valid-uuid'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 3)

    def test_blank_filter_parameters_ignored(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(
            reverse('catalog:product_list'),
            {'q': '   ', 'category': '', 'status': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 3)

    def test_form_preserves_chosen_values(self):
        self.client.login(username='admin1', password=PASSWORD)
        response = self.client.get(
            reverse('catalog:product_list'),
            {
                'q': 'ThinkPad',
                'category': str(self.cat_laptops.pk),
                'status': 'active',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="ThinkPad"')
        self.assertContains(response, f'value="{self.cat_laptops.pk}" selected')
        self.assertContains(response, 'value="active" selected')

class ProductStockDisplayTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin1', 'admin1@esims.local', PASSWORD, role='ADMIN'
        )
        self.staff = User.objects.create_user(
            'staff1', 'staff1@esims.local', PASSWORD, role='STAFF'
        )
        self.cat1 = Category.objects.create(name='Monitors', status=Category.Status.ACTIVE)
        self.cat2 = Category.objects.create(name='Keyboards', status=Category.Status.ACTIVE)

        self.p1 = Product.objects.create(
            sku='MON-001',
            name='Dell 27 Inch 4K',
            category=self.cat1,
            price=Decimal('399.99'),
            quantity_in_stock=123,
            status=Product.Status.ACTIVE,
        )
        self.p2 = Product.objects.create(
            sku='MON-002',
            name='LG UltraWide 34',
            category=self.cat1,
            price=Decimal('699.99'),
            quantity_in_stock=0,
            status=Product.Status.ACTIVE,
        )
        self.p3 = Product.objects.create(
            sku='KB-001',
            name='Keychron K2',
            category=self.cat2,
            price=Decimal('79.99'),
            quantity_in_stock=55,
            status=Product.Status.ACTIVE,
        )

    def test_stock_quantity_clearly_labelled_and_visible_to_staff(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'In stock')
        self.assertContains(response, '123')
        self.assertContains(response, '0')
        self.assertContains(response, '55')

    def test_stock_quantity_visible_to_admin(self):
        self.client.login(username='admin1', password=PASSWORD)
        response = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'In stock')
        self.assertContains(response, '123')
        self.assertContains(response, '0')
        self.assertContains(response, '55')

    def test_stock_quantity_correct_when_filtered(self):
        self.client.login(username='staff1', password=PASSWORD)
        response = self.client.get(
            reverse('catalog:product_list'), {'category': str(self.cat1.pk)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '123')
        self.assertContains(response, '0')
        self.assertNotContains(response, 'Keychron K2')

        response_kb = self.client.get(
            reverse('catalog:product_list'), {'q': 'Keychron'}
        )
        self.assertEqual(response_kb.status_code, 200)
        self.assertContains(response_kb, '55')
        self.assertNotContains(response_kb, 'Dell 27 Inch 4K')
        self.assertNotContains(response_kb, 'LG UltraWide 34')

class ProductPaginationSelectorTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin1', 'admin1@esims.local', PASSWORD, role='ADMIN'
        )
        self.category = Category.objects.create(name='Pagination')
        self.client.force_login(self.admin)

    def make_product(self, number, **overrides):
        values = {
            'sku': f'PAGE-{number:04d}',
            'name': f'Pagination Product {number:04d}',
            'category': self.category,
            'price': Decimal('10.00'),
            'status': Product.Status.ACTIVE,
        }
        values.update(overrides)
        return Product.objects.create(**values)

    def test_next_page_preserves_search_filters(self):
        for number in range(26):
            self.make_product(number)

        response = self.client.get(reverse('catalog:product_list'), {
            'q': 'Pagination', 'category': str(self.category.pk), 'status': 'active',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Page 1 of 2')
        self.assertContains(response, f'q=Pagination&amp;category={self.category.pk}&amp;status=active&amp;page=2')

    def test_invalid_and_out_of_range_pages_do_not_crash(self):
        for number in range(30):
            self.make_product(number)

        invalid = self.client.get(reverse('catalog:product_list'), {'page': 'abc'})
        out_of_range = self.client.get(reverse('catalog:product_list'), {'page': '999'})

        self.assertEqual(invalid.status_code, 200)
        self.assertEqual(invalid.context['page_obj'].number, 1)
        self.assertEqual(out_of_range.status_code, 200)
        self.assertEqual(out_of_range.context['page_obj'].number, 2)


    def test_query_count_does_not_grow_with_product_count(self):
        for number in range(5):
            self.make_product(number)
        with CaptureQueriesContext(connection) as small_capture:
            self.client.get(reverse('catalog:product_list'))
        for number in range(5, 50):
            self.make_product(number)
        with CaptureQueriesContext(connection) as large_capture:
            self.client.get(reverse('catalog:product_list'))

        self.assertEqual(len(small_capture), len(large_capture))

    def test_search_response_with_500_products_is_under_two_seconds(self):
        Product.objects.bulk_create([
            Product(
                sku=f'TIME-{number:04d}', name=f'Timing Product {number:04d}',
                category=self.category, price=Decimal('10.00'),
            )
            for number in range(500)
        ])
        started = time.perf_counter()

        response = self.client.get(reverse('catalog:product_list'), {'q': 'Timing'})

        self.assertEqual(response.status_code, 200)
        self.assertLess(time.perf_counter() - started, 2.0)


class CatalogPermissionMatrixTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'matrix-admin', 'matrix-admin@esims.local', PASSWORD, role='ADMIN',
        )
        self.staff = User.objects.create_user(
            'matrix-staff', 'matrix-staff@esims.local', PASSWORD, role='STAFF',
        )
        self.category = Category.objects.create(name='Permission Matrix')
        self.product = Product.objects.create(
            sku='MATRIX-001', name='Permission Test Product', category=self.category,
            price=Decimal('10.00'),
        )

    def test_every_named_catalog_url_for_anonymous_staff_and_admin(self):
        urls = {
            'product_root': '/catalog/',
            'product_list': reverse('catalog:product_list'),
            'product_add': reverse('catalog:product_add'),
            'product_edit': reverse('catalog:product_edit', args=[self.product.pk]),
            'product_disable': reverse('catalog:product_disable', args=[self.product.pk]),
            'category_list': reverse('catalog:category_list'),
            'category_add': reverse('catalog:category_add'),
            'category_edit': reverse('catalog:category_edit', args=[self.category.pk]),
        }
        cases = (
            ('anonymous', None),
            ('staff', self.staff),
            ('admin', self.admin),
        )
        staff_allowed = {'product_root', 'product_list'}

        for role_name, user in cases:
            if user is None:
                self.client.logout()
            else:
                self.client.force_login(user)
            for url_name, path in urls.items():
                with self.subTest(role=role_name, url=url_name):
                    response = self.client.get(path)
                    if role_name == 'admin' or (role_name == 'staff' and url_name in staff_allowed):
                        self.assertEqual(response.status_code, 200)
                    else:
                        self.assertEqual(response.status_code, 302)
