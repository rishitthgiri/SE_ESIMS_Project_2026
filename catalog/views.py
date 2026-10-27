from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, ProductForm
from .models import Category, Product

# TEMPORARY until accounts/decorators.py (Roopa) is merged.
# Then delete this line and use:
#   from accounts.decorators import admin_required
admin_required = user_passes_test(lambda u: u.is_authenticated and u.is_admin_role)


@login_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'catalog/product_list.html', {'products': products})


@login_required
@admin_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added.')
            return redirect('catalog:product_list')
    else:
        form = ProductForm()
    return render(request, 'catalog/product_form.html', {'form': form, 'title': 'Add product'})


@login_required
@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('catalog:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'catalog/product_form.html', {'form': form, 'title': 'Edit product'})


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