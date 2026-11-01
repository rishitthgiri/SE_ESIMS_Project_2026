"""Shared fixtures for the transactions tests."""
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Category, Product
from suppliers.models import Supplier

User = get_user_model()


def new_token():
    """A fresh form token, like the one a browser receives with every stock form."""
    return str(uuid.uuid4())


class StockTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('staff1', 'staff1@example.com', 'pass12345', role='STAFF')
        cls.admin = User.objects.create_user('admin1', 'admin1@example.com', 'pass12345', role='ADMIN')
        cls.category = Category.objects.create(name='Mobiles')
        cls.supplier = Supplier.objects.create(name='Acme Distributors', contact='acme@example.com')
        cls.product = Product.objects.create(
            sku='MOB-001', name='Phone X', category=cls.category,
            price='19999.00', quantity_in_stock=5, reorder_threshold=2,
        )

    def stock(self, product=None):
        return Product.objects.get(pk=(product or self.product).pk).quantity_in_stock
