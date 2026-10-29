from django import forms

from suppliers.models import Supplier
from .models import Category, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'status']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        clash = Category.objects.filter(name__iexact=name)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('A category with this name already exists.')
        return name


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'category', 'price', 'reorder_threshold', 'supplier', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Category choices: active categories only (keep current instance's category on edit even if disabled)
        category_qs = Category.objects.filter(status=Category.Status.ACTIVE)
        if self.instance and self.instance.pk and self.instance.category_id:
            category_qs = (category_qs | Category.objects.filter(pk=self.instance.category_id)).distinct()
        self.fields['category'].queryset = category_qs

        # Supplier choices: active suppliers only, supplier optional (keep current instance's supplier on edit if disabled)
        supplier_qs = Supplier.objects.filter(status=Supplier.Status.ACTIVE)
        if self.instance and self.instance.pk and self.instance.supplier_id:
            supplier_qs = (supplier_qs | Supplier.objects.filter(pk=self.instance.supplier_id)).distinct()
        self.fields['supplier'].queryset = supplier_qs
        self.fields['supplier'].required = False

        # Apply Bootstrap classes
        for field in self.fields.values():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

    def clean_sku(self):
        sku = self.cleaned_data.get('sku', '').strip()
        if not sku:
            raise forms.ValidationError('SKU is required.')
        clash = Product.objects.filter(sku__iexact=sku)
        if self.instance and self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('A product with this SKU already exists.')
        return sku

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Name is required.')
        return name

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Price must be greater than or equal to 0.')
        return price

    def clean_reorder_threshold(self):
        threshold = self.cleaned_data.get('reorder_threshold')
        if threshold is not None and threshold < 0:
            raise forms.ValidationError('Reorder threshold must be greater than or equal to 0.')
        return threshold