from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CategoryForm, ProductForm
from .models import Category, Product
from .selectors import search_products
from .services import disable_product

# TEMPORARY until accounts/decorators.py (Roopa) is merged.
# Then delete this line and use:
#   from accounts.decorators import admin_required
admin_required = user_passes_test(lambda u: u.is_authenticated and u.is_admin_role)


@login_required
def product_list(request):
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    status = request.GET.get('status', '').strip()
    page_obj = Paginator(search_products(q, category_id, status), 25).get_page(
        request.GET.get('page')
    )
    categories = Category.objects.all()
    is_filtered = bool(q or category_id or status)
    context = {
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'categories': categories,
        'q': q,
        'selected_category': category_id,
        'selected_status': status,
        'is_filtered': is_filtered,
    }
    return render(request, 'catalog/product_list.html', context)


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
@require_http_methods(['GET', 'POST'])
def product_disable(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        if not disable_product(product):
            messages.info(request, 'Product is already disabled.')
        else:
            messages.success(request, 'Product disabled.')
        return redirect('catalog:product_list')

    return render(request, 'catalog/product_confirm_disable.html', {'product': product})


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
