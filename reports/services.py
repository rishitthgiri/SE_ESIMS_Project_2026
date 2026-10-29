"""Report logic (ESIMS-31 / FR-018 and ESIMS-32 / FR-019), independent of the views (NFR-006).

Sales = StockTransaction rows of type OUT. The amount of a sale is quantity x the product's
CURRENT price, because transactions do not store a price snapshot (see docs/DEVIATIONS.md).
"""
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum

from catalog.models import Product
from transactions.models import StockTransaction

MONEY = DecimalField(max_digits=14, decimal_places=2)
ZERO = Decimal('0.00')


def _in_range(prefix, start, end):
    """Q object limiting `<prefix>timestamp` to start..end (both dates inclusive)."""
    q = Q()
    if start:
        q &= Q(**{f'{prefix}timestamp__date__gte': start})
    if end:
        q &= Q(**{f'{prefix}timestamp__date__lte': end})
    return q


def sales_queryset(start, end):
    """Stock-out transactions in the date range, newest first, with an `amount` per row."""
    return (
        StockTransaction.objects
        .filter(transaction_type=StockTransaction.Type.OUT)
        .filter(_in_range('', start, end))
        .select_related('product', 'user')
        .annotate(amount=ExpressionWrapper(F('quantity') * F('product__price'), output_field=MONEY))
        .order_by('-timestamp', '-id')
    )


def sales_totals(start, end):
    agg = (
        StockTransaction.objects
        .filter(transaction_type=StockTransaction.Type.OUT)
        .filter(_in_range('', start, end))
        .aggregate(
            units=Sum('quantity'),
            total=Sum(ExpressionWrapper(F('quantity') * F('product__price'), output_field=MONEY)),
        )
    )
    return {'units': agg['units'] or 0, 'amount': agg['total'] or ZERO}


def stock_queryset(start, end):
    """Every product with its current stock, stock value and the units moved in the range."""
    ins = Q(transactions__transaction_type=StockTransaction.Type.IN) & _in_range('transactions__', start, end)
    outs = Q(transactions__transaction_type=StockTransaction.Type.OUT) & _in_range('transactions__', start, end)
    return (
        Product.objects
        .select_related('category')
        .annotate(
            stock_value=ExpressionWrapper(F('quantity_in_stock') * F('price'), output_field=MONEY),
            units_in=Sum('transactions__quantity', filter=ins),
            units_out=Sum('transactions__quantity', filter=outs),
        )
        .order_by('name', 'sku')
    )


def stock_total_value():
    agg = Product.objects.aggregate(
        total=Sum(ExpressionWrapper(F('quantity_in_stock') * F('price'), output_field=MONEY)))
    return agg['total'] or ZERO


def top_selling(start, end, limit=10):
    """Products ranked by units sold (stock-out) in the range. Ties broken by name."""
    sold = Q(transactions__transaction_type=StockTransaction.Type.OUT) & _in_range('transactions__', start, end)
    return list(
        Product.objects
        .select_related('category')
        .annotate(
            units_sold=Sum('transactions__quantity', filter=sold),
            revenue=Sum(
                ExpressionWrapper(F('transactions__quantity') * F('price'), output_field=MONEY),
                filter=sold),
        )
        .filter(units_sold__gt=0)
        .order_by('-units_sold', 'name')[:limit]
    )
