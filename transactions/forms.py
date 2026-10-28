from django import forms

from catalog.models import Product
from esims.validation import StrictIntegerField
from suppliers.models import Supplier

from .services import MAX_QUANTITY


class ProductChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.sku} - {obj.name} (in stock: {obj.quantity_in_stock})'


def _quantity_field():
    # ESIMS-08: digits only - rejects '1e3', '+5', '5.0', ' 5 ', '-1', text, empty, 0 and > MAX_QUANTITY.
    return StrictIntegerField(
        min_value=1,
        max_value=MAX_QUANTITY,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        error_messages={'invalid': 'Enter a whole number.'},
    )


class StockInForm(forms.Form):
    product = ProductChoiceField(queryset=Product.objects.none(),
                                 widget=forms.Select(attrs={'class': 'form-select'}))
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.none(),
                                      widget=forms.Select(attrs={'class': 'form-select'}))
    quantity = _quantity_field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only ACTIVE products/suppliers can be used in new transactions.
        self.fields['product'].queryset = Product.objects.filter(status=Product.Status.ACTIVE)
        self.fields['supplier'].queryset = Supplier.objects.filter(status=Supplier.Status.ACTIVE)


class StockOutForm(forms.Form):
    product = ProductChoiceField(queryset=Product.objects.none(),
                                 widget=forms.Select(attrs={'class': 'form-select'}))
    quantity = _quantity_field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(status=Product.Status.ACTIVE)
