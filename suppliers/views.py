from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from functools import wraps

from django.views.decorators.http import require_POST

from transactions.models import StockTransaction

from .forms import SupplierForm
from .models import Supplier

def _admin_only(view):
    """Anonymous -> login page, Staff -> 403, Admin -> view (same as AdminRequiredMixin)."""
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_role:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


@_admin_only
def supplier_list(request):
    suppliers = Supplier.objects.all()
    status = request.GET.get('status', '')
    if status in Supplier.Status.values:
        suppliers = suppliers.filter(status=status)
    return render(request, 'suppliers/supplier_list.html', {'suppliers': suppliers, 'status': status})


@_admin_only
def supplier_add(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        supplier = form.save()
        messages.success(request, f'Supplier "{supplier.name}" added.')
        return redirect('suppliers:list')
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Add supplier'})


@_admin_only
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Supplier "{supplier.name}" updated.')
        return redirect('suppliers:list')
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Edit supplier'})


@_admin_only
@require_POST
def supplier_disable(request, pk):
    """'Remove' = soft delete. History keeps pointing at the supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.status = Supplier.Status.DISABLED
    supplier.save(update_fields=['status'])
    messages.success(request, f'Supplier "{supplier.name}" disabled. It can no longer be used for stock-in.')
    return redirect('suppliers:list')


@_admin_only
def supplier_detail(request, pk):
    """ESIMS-28: stock-ins received from this supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    stock_ins = (
        StockTransaction.objects.filter(supplier=supplier, transaction_type=StockTransaction.Type.IN)
        .select_related('product', 'user')[:50]
    )
    return render(request, 'suppliers/supplier_detail.html', {'supplier': supplier, 'stock_ins': stock_ins})
