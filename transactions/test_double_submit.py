"""ESIMS-23: duplicate form submission is ignored (NFR-004, ST-REL-01).

Run: python manage.py test transactions.test_double_submit -v 2
"""
import uuid
from unittest import mock

from django.db import IntegrityError, transaction
from django.urls import reverse

from . import services
from .models import StockTransaction
from .testutils import StockTestBase, new_token


class DoubleSubmitServiceTests(StockTestBase):
    def test_same_token_twice_for_stock_in_records_only_one(self):
        """ST-REL-01 / NFR-004"""
        token = uuid.uuid4()
        first = services.record_stock_in(product=self.product, supplier=self.supplier, quantity=4,
                                         user=self.staff, request_token=token)
        with self.assertRaises(services.DuplicateSubmission) as ctx:
            services.record_stock_in(product=self.product, supplier=self.supplier, quantity=4,
                                     user=self.staff, request_token=token)
        self.assertEqual(ctx.exception.transaction, first)
        self.assertEqual(self.stock(), 9)                      # 5 + 4, applied once
        self.assertEqual(StockTransaction.objects.count(), 1)

    def test_same_token_twice_for_stock_out_records_only_one(self):
        token = uuid.uuid4()
        first = services.record_stock_out(product=self.product, quantity=2, user=self.staff, request_token=token)
        with self.assertRaises(services.DuplicateSubmission) as ctx:
            services.record_stock_out(product=self.product, quantity=2, user=self.staff, request_token=token)
        self.assertEqual(ctx.exception.transaction, first)
        self.assertEqual(self.stock(), 3)                      # 5 - 2, applied once
        self.assertEqual(StockTransaction.objects.count(), 1)

    def test_duplicate_is_reported_even_when_stock_would_now_be_too_low(self):
        """A retry of a successful sale must say 'already recorded', not 'insufficient stock'"""
        token = uuid.uuid4()
        services.record_stock_out(product=self.product, quantity=5, user=self.staff, request_token=token)
        with self.assertRaises(services.DuplicateSubmission):
            services.record_stock_out(product=self.product, quantity=5, user=self.staff, request_token=token)
        self.assertEqual(self.stock(), 0)

    def test_different_tokens_are_two_genuine_transactions(self):
        services.record_stock_out(product=self.product, quantity=1, user=self.staff, request_token=uuid.uuid4())
        services.record_stock_out(product=self.product, quantity=1, user=self.staff, request_token=uuid.uuid4())
        self.assertEqual(self.stock(), 3)
        self.assertEqual(StockTransaction.objects.count(), 2)

    def test_no_token_still_works(self):
        services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        services.record_stock_out(product=self.product, quantity=1, user=self.staff)
        self.assertEqual(self.stock(), 3)

    def test_token_cannot_be_reused_by_another_user_or_for_another_action(self):
        token = uuid.uuid4()
        services.record_stock_out(product=self.product, quantity=1, user=self.staff, request_token=token)
        with self.assertRaises(services.InvalidStockOperation):       # other user
            services.record_stock_out(product=self.product, quantity=1, user=self.admin, request_token=token)
        with self.assertRaises(services.InvalidStockOperation):       # other action (stock-in)
            services.record_stock_in(product=self.product, supplier=self.supplier, quantity=1,
                                     user=self.staff, request_token=token)
        self.assertEqual(self.stock(), 4)
        self.assertEqual(StockTransaction.objects.count(), 1)

    def test_malformed_token_is_rejected(self):
        for bad in ('abc', 123, 'not-a-uuid'):
            with self.assertRaises(services.InvalidStockOperation):
                services.record_stock_out(product=self.product, quantity=1, user=self.staff, request_token=bad)
        self.assertEqual(self.stock(), 5)

    def test_database_enforces_unique_token(self):
        token = uuid.uuid4()
        services.record_stock_out(product=self.product, quantity=1, user=self.staff, request_token=token)
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockTransaction.objects.create(product=self.product, user=self.staff, transaction_type='OUT',
                                            quantity=1, request_token=token)

    def test_race_where_the_check_misses_is_still_caught_and_rolled_back(self):
        """Two requests pass the 'already used?' check at once: the unique column stops the second
        one, and its stock change is rolled back."""
        token = uuid.uuid4()
        services.record_stock_out(product=self.product, quantity=2, user=self.staff, request_token=token)
        real_find = services._find_token
        calls = {'n': 0}

        def blind_first_check(request_token):
            calls['n'] += 1
            return None if calls['n'] == 1 else real_find(request_token)

        with mock.patch.object(services, '_find_token', side_effect=blind_first_check):
            with self.assertRaises(services.DuplicateSubmission):
                services.record_stock_out(product=self.product, quantity=2, user=self.staff, request_token=token)
        self.assertEqual(self.stock(), 3)                      # not 1: the second deduction was rolled back
        self.assertEqual(StockTransaction.objects.count(), 1)


class DoubleSubmitViewTests(StockTestBase):
    def setUp(self):
        self.client.force_login(self.staff)

    def test_forms_carry_a_fresh_hidden_token_each_time(self):
        for name in ('transactions:stock_in', 'transactions:stock_out'):
            a = self.client.get(reverse(name)).context['form']['request_token'].value()
            b = self.client.get(reverse(name)).context['form']['request_token'].value()
            self.assertNotEqual(a, b, name)
            self.assertIn('name="request_token"', self.client.get(reverse(name)).content.decode())

    def test_page_has_the_double_click_guard(self):
        body = self.client.get(reverse('transactions:stock_out')).content.decode()
        self.assertIn('id="stock-form"', body)
        self.assertIn('dataset.submitted', body)

    def test_double_post_of_stock_out_creates_one_record(self):
        data = {'product': self.product.pk, 'quantity': 2, 'request_token': new_token()}
        self.client.post(reverse('transactions:stock_out'), data)
        resp = self.client.post(reverse('transactions:stock_out'), data, follow=True)    # the "second click"
        self.assertEqual(StockTransaction.objects.count(), 1)
        self.assertEqual(self.stock(), 3)
        self.assertContains(resp, 'already recorded')
        self.assertContains(resp, 'not saved twice')

    def test_double_post_of_stock_in_creates_one_record(self):
        data = {'product': self.product.pk, 'supplier': self.supplier.pk, 'quantity': 4, 'request_token': new_token()}
        self.client.post(reverse('transactions:stock_in'), data)
        resp = self.client.post(reverse('transactions:stock_in'), data, follow=True)
        self.assertEqual(StockTransaction.objects.count(), 1)
        self.assertEqual(self.stock(), 9)
        self.assertContains(resp, 'already recorded')

    def test_rejected_sale_does_not_use_up_the_token(self):
        token = new_token()
        resp = self.client.post(reverse('transactions:stock_out'),
                                {'product': self.product.pk, 'quantity': 6, 'request_token': token})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, token)                        # same token still on the re-shown form
        resp = self.client.post(reverse('transactions:stock_out'),
                                {'product': self.product.pk, 'quantity': 2, 'request_token': token}, follow=True)
        self.assertContains(resp, 'Stock-out recorded')
        self.assertEqual(self.stock(), 3)

    def test_post_without_a_token_is_refused(self):
        resp = self.client.post(reverse('transactions:stock_out'), {'product': self.product.pk, 'quantity': 1})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'expired or was already used')
        self.assertEqual(StockTransaction.objects.count(), 0)
        self.assertEqual(self.stock(), 5)

    def test_post_with_a_garbage_token_is_refused(self):
        resp = self.client.post(reverse('transactions:stock_out'),
                                {'product': self.product.pk, 'quantity': 1, 'request_token': "'; DROP TABLE x;--"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(StockTransaction.objects.count(), 0)
