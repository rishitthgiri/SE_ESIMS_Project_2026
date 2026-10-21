from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'price', 'quantity_in_stock', 'reorder_threshold', 'status')
    list_filter = ('status', 'category')
    search_fields = ('sku', 'name')
