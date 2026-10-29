import csv
from decimal import Decimal
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render

from . import services
from .alerts import low_stock_products
from .forms import DateRangeForm

SALES_ROWS_ON_PAGE = 500  # the CSV export always has every row


def _admin_only(view):
    """Anonymous -> login page, Staff -> 403, Admin -> view (agreement section 5: reports are Admin only)."""
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_role:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def _csv_safe(value):
    """Stop spreadsheet formula injection: text starting with = + - @ is prefixed with an apostrophe."""
    if isinstance(value, str) and value[:1] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + value
    return value


def _money(value):
    return f'{Decimal(value):.2f}'


def _csv_response(filename, header, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow([_csv_safe(cell) for cell in row])
    return response


@login_required
def low_stock(request):
    """ESIMS-29: visible to Staff and Admin (agreement section 5)."""
    return render(request, 'reports/low_stock.html', {'products': low_stock_products()})


@_admin_only
def sales_report(request):
    """ESIMS-31 / FR-018 / UC-09: stock and sales report for a date range (default: last 30 days)."""
    form = DateRangeForm.from_request(request, default_days=30)
    context = {'form': form}
    if form.is_valid():
        start, end = form.cleaned_data['start'], form.cleaned_data['end']
        export = request.GET.get('export')
        if export == 'sales':
            rows = [
                (t.transaction_id, t.product.name, t.quantity, _money(t.amount),
                 t.timestamp.strftime('%Y-%m-%d %H:%M'), t.user.username)
                for t in services.sales_queryset(start, end)
            ]
            return _csv_response('sales_report.csv', [
                'Transaction reference', 'Product', 'Quantity sold', 'Sale amount', 'Date', 'Staff member'], rows)
        if export == 'stock':
            rows = [
                (p.name, p.sku, p.category.name, p.quantity_in_stock, p.reorder_threshold, _money(p.stock_value),
                 p.units_in or 0, p.units_out or 0)
                for p in services.stock_queryset(start, end)
            ]
            return _csv_response('stock_report.csv', [
                'Product', 'SKU', 'Category', 'Current stock', 'Reorder threshold', 'Stock value',
                'Units in (range)', 'Units out (range)'], rows)
        context.update(
            start=start, end=end,
            sales=services.sales_queryset(start, end)[:SALES_ROWS_ON_PAGE],
            sales_limit=SALES_ROWS_ON_PAGE,
            totals=services.sales_totals(start, end),
            stock=services.stock_queryset(start, end),
            stock_total=services.stock_total_value(),
            query=request.GET.urlencode() if request.GET else
            f'start={start:%Y-%m-%d}&end={end:%Y-%m-%d}',
        )
    return render(request, 'reports/sales_report.html', context)


@_admin_only
def top_selling(request):
    """ESIMS-32 / FR-019: products ranked by units sold. No dates = all recorded sales."""
    form = DateRangeForm.from_request(request)
    context = {'form': form}
    if form.is_valid():
        context['products'] = services.top_selling(form.cleaned_data['start'], form.cleaned_data['end'])
    return render(request, 'reports/top_selling.html', context)
