"""Measure product-list responses for the local SQLite search workload."""
import math
import statistics
import time
import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.test import Client

from catalog.models import Category, Product
from catalog.selectors import search_products


class Command(BaseCommand):
    help = 'Time 200 product-list requests as a logged-in admin user.'

    def handle(self, *args, **options):
        category = Category.objects.filter(name='PERF-Test').first()
        if category is None or not search_products(category=str(category.pk), status='active').exists():
            raise CommandError('Seed active PERF-Test products first with seed_demo_products --yes.')

        User = get_user_model()
        username = f'measure-{uuid.uuid4().hex}'
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.invalid',
            password=uuid.uuid4().hex,
            role=User.Role.ADMIN,
        )
        client = Client(HTTP_HOST='localhost')
        client.force_login(user)
        query_terms = ['', 'PERF-00001', 'Performance Demo', 'missing-search-term']
        page_numbers = [1, 2, 5, 20, 100, 200]
        durations = []
        try:
            for index in range(200):
                params = {
                    'q': query_terms[index % len(query_terms)],
                    'category': str(category.pk),
                    'status': Product.Status.ACTIVE,
                    'page': page_numbers[index % len(page_numbers)],
                }
                started = time.perf_counter()
                response = client.get('/catalog/products/', params)
                durations.append(time.perf_counter() - started)
                if response.status_code != 200:
                    raise CommandError(f'Search request returned HTTP {response.status_code}.')
        finally:
            user.delete()

        ordered = sorted(durations)
        p95 = ordered[math.ceil(0.95 * len(ordered)) - 1]
        result = 'PASS' if p95 < 2.0 else 'FAIL'
        self.stdout.write(f'count: {len(durations)}')
        self.stdout.write(f'mean: {statistics.mean(durations):.4f}s')
        self.stdout.write(f'median: {statistics.median(durations):.4f}s')
        self.stdout.write(f'p95: {p95:.4f}s')
        self.stdout.write(f'max: {max(durations):.4f}s')
        self.stdout.write(f'{result}: p95 < 2.0 seconds')
