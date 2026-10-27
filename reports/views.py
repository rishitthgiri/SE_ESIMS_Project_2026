from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .alerts import low_stock_products


@login_required
def low_stock(request):
    """ESIMS-29: visible to Staff and Admin (agreement section 5)."""
    return render(request, 'reports/low_stock.html', {'products': low_stock_products()})
