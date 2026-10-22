from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm
from .models import Category

# TEMPORARY until accounts/decorators.py (Roopa) is merged.
# Then delete this line and use:
#   from accounts.decorators import admin_required
admin_required = user_passes_test(lambda u: u.is_authenticated and u.is_admin_role)


@login_required
@admin_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'catalog/category_list.html', {'categories': categories})


@login_required
@admin_required
def category_add(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category added.')
        return redirect('catalog:category_list')
    return render(request, 'catalog/category_form.html', {'form': form, 'title': 'Add category'})


@login_required
@admin_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('catalog:category_list')
    return render(request, 'catalog/category_form.html', {'form': form, 'title': 'Edit category'})