"""Create clearly marked catalog rows for local search measurements."""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Category, Product


class Command(BaseCommand):
    help = 'Create or disable PERF-Test products for local search measurements.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5000)
        parser.add_argument('--clear', action='store_true', help='Disable existing PERF-Test products.')
        parser.add_argument('--yes', action='store_true', help='Confirm this local demo-data operation.')

    def handle(self, *args, **options):
        if not options['yes']:
            raise CommandError('Refusing to change demo data without --yes.')
        if options['count'] < 0:
            raise CommandError('--count must be zero or greater.')

        category = Category.objects.filter(name='PERF-Test').first()
        if options['clear']:
            if category is None:
                self.stdout.write('No PERF-Test category or products found.')
                return
            changed = Product.objects.filter(
                category=category, sku__startswith='PERF-', status=Product.Status.ACTIVE,
            ).update(status=Product.Status.DISABLED)
            self.stdout.write(self.style.SUCCESS(f'Disabled {changed} PERF-Test products.'))
            return

        if category is None:
            category = Category.objects.create(name='PERF-Test')
        existing = set(Product.objects.filter(
            sku__in=[f'PERF-{number:05d}' for number in range(options['count'])]
        ).values_list('sku', flat=True))
        products = [
            Product(
                sku=f'PERF-{number:05d}',
                name=f'Performance Demo Product {number:05d}',
                category=category,
                price=Decimal('10.00'),
                reorder_threshold=5,
                status=Product.Status.ACTIVE,
            )
            for number in range(options['count'])
            if f'PERF-{number:05d}' not in existing
        ]
        with transaction.atomic():
            Product.objects.bulk_create(products, batch_size=1000)
            Product.objects.filter(
                category=category,
                sku__in=[f'PERF-{number:05d}' for number in range(options['count'])],
            ).update(status=Product.Status.ACTIVE)
        self.stdout.write(self.style.SUCCESS(
            f'Created {len(products)} PERF-Test products; '
            f'{options["count"]} requested SKUs are active.'
        ))
