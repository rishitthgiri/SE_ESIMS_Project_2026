"""Supplier management (ESIMS-27 / FR-015 / UC-08). Admin only.

"Remove" means status='disabled' (soft delete) so old stock-in
transactions keep pointing at the supplier.
"""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SupplierForm
from .models import Supplier


# Temporary admin check. When Roopa's accounts/decorators.py admin_required
# is on main, swap this for it.
admin_only = user_passes_test(lambda u: u.is_authenticated and u.is_admin_role)


@admin_only
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'suppliers/supplier_list.html', {'suppliers': suppliers})


@admin_only
def supplier_add(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        supplier = form.save()
        messages.success(request, f'Supplier "{supplier.name}" added.')
        return redirect('suppliers:list')
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Add supplier'})


@admin_only
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Supplier "{supplier.name}" updated.')
        return redirect('suppliers:list')
    return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Edit supplier'})


@admin_only
@require_POST
def supplier_disable(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.status = Supplier.Status.DISABLED
    supplier.save(update_fields=['status'])
    messages.success(request, f'Supplier "{supplier.name}" disabled.')
    return redirect('suppliers:list')
