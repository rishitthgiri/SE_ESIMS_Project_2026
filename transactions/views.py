from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from . import services
from .forms import StockInForm, StockOutForm
from .models import StockTransaction


@login_required
@require_http_methods(['GET', 'POST'])
def stock_in(request):
    """ESIMS-18: Staff/Admin records a purchase against a registered supplier."""
    form = StockInForm(request.POST) if request.method == 'POST' else StockInForm()
    if request.method == 'POST' and form.is_valid():
        try:
            txn = services.record_stock_in(
                product=form.cleaned_data['product'],
                supplier=form.cleaned_data['supplier'],
                quantity=form.cleaned_data['quantity'],
                user=request.user,
            )
        except services.StockError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(
                request,
                f'Stock-in recorded. Transaction ID: {txn.transaction_id}. '
                f'{txn.product.name} stock is now {txn.product.quantity_in_stock}.',
            )
            return redirect('transactions:list')
    return render(request, 'transactions/stock_in.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def stock_out(request):
    """ESIMS-19/20: Staff/Admin records a sale. Over-sales are rejected."""
    form = StockOutForm(request.POST) if request.method == 'POST' else StockOutForm()
    if request.method == 'POST' and form.is_valid():
        try:
            txn = services.record_stock_out(
                product=form.cleaned_data['product'],
                quantity=form.cleaned_data['quantity'],
                user=request.user,
            )
        except services.InsufficientStock as exc:
            form.add_error('quantity', str(exc))
        except services.StockError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(
                request,
                f'Stock-out recorded. Transaction ID: {txn.transaction_id}. '
                f'{txn.product.name} stock is now {txn.product.quantity_in_stock}.',
            )
            return redirect('transactions:list')
    return render(request, 'transactions/stock_out.html', {'form': form})


@login_required
def transaction_list(request):
    """ESIMS-21: list of transactions with their unique IDs.

    Staff see their own transactions; Administrators see all of them.
    (The full Admin audit list is ESIMS-22, Sprint 2.)
    """
    qs = StockTransaction.objects.select_related('product', 'supplier', 'user')
    if not request.user.is_admin_role:
        qs = qs.filter(user=request.user)
    txn_type = request.GET.get('type')
    if txn_type in StockTransaction.Type.values:
        qs = qs.filter(transaction_type=txn_type)
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'transactions/transaction_list.html', {'page': page, 'txn_type': txn_type})
