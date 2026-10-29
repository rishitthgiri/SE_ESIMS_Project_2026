"""ESIMS-33 / SEC-005 / ST-SEC-05: nothing sensitive is reachable without logging in.

The test walks EVERY url in the project, so a view added later without login protection
makes this test fail instead of silently leaking supplier or pricing data.
"""
import re
import uuid

from django.test import TestCase
from django.urls import URLResolver, get_resolver

from accounts.testutils import make_admin
from catalog.models import Category, Product
from suppliers.models import Supplier
from transactions import services as stock

# The only pages a logged-out visitor may open (no supplier or pricing data on them).
PUBLIC_PATHS = {'login/', 'logout/', 'health/'}

SECRETS = ['Zeta Secret Supplier', 'zeta-contact@secret.test', 'Hidden Gadget', '987654.32', 'HG-SECRET-1']


def all_paths(patterns=None, prefix=''):
    patterns = patterns if patterns is not None else get_resolver().url_patterns
    for entry in patterns:
        route = str(entry.pattern)
        if isinstance(entry, URLResolver):
            if route.startswith('^'):   # regex mounts (django admin internals) are covered below
                continue
            yield from all_paths(entry.url_patterns, prefix + route)
        elif not route.startswith('^'):
            yield prefix + route


def concrete(path, pk):
    path = re.sub(r'<uuid:\w+>', str(pk), path)
    path = re.sub(r'<int:\w+>', '1', path)
    return '/' + re.sub(r'<(?:str|slug):\w+>', 'x', path)


class LoggedOutAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_admin('boss')
        cls.supplier = Supplier.objects.create(name=SECRETS[0], contact=SECRETS[1])
        cat = Category.objects.create(name='Hidden Category')
        cls.product = Product.objects.create(
            sku=SECRETS[4], name=SECRETS[2], category=cat, price=SECRETS[3], quantity_in_stock=5, reorder_threshold=1)
        stock.record_stock_in(product=cls.product, supplier=cls.supplier, quantity=3, user=cls.admin)

    def protected_urls(self):
        paths = [p for p in set(all_paths()) if p not in PUBLIC_PATHS and not p.startswith('admin/')]
        return sorted(concrete(p, self.supplier.pk) for p in paths)

    def test_crawler_actually_finds_the_app_urls(self):
        urls = self.protected_urls()
        self.assertGreater(len(urls), 12, urls)
        for expected in ('/suppliers/', '/catalog/', '/transactions/', '/reports/sales/', '/reports/low-stock/'):
            self.assertIn(expected, urls)

    def test_every_page_redirects_logged_out_visitors_to_login(self):
        for url in self.protected_urls():
            for method in ('get', 'post'):
                r = getattr(self.client, method)(url)
                self.assertEqual(r.status_code, 302, f'{method.upper()} {url} -> {r.status_code}')
                self.assertIn('/login/', r['Location'], url)

    def test_no_sensitive_data_in_any_response(self):
        pages = self.protected_urls() + ['/login/']
        for url in pages:
            for follow in (False, True):
                body = self.client.get(url, follow=follow).content.decode()
                for secret in SECRETS:
                    self.assertNotIn(secret, body, f'{secret!r} leaked on {url} (follow={follow})')

    def test_django_admin_requires_login_too(self):
        for url in ('/admin/', '/admin/suppliers/supplier/', '/admin/catalog/product/'):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn('/admin/login/', r['Location'])
