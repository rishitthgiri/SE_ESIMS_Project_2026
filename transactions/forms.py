import uuid

from django import forms

from catalog.models import Product
from esims.validation import SanitizedCharField, StrictIntegerField
from suppliers.models import Supplier

from .models import StockTransaction
from .services import MAX_QUANTITY

TOKEN_ERROR = 'This form has expired or was already used. Please reload the page and try again.'


class ProductChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.sku} - {obj.name} (in stock: {obj.quantity_in_stock})'


def _quantity_field():
    # StrictIntegerField (ESIMS-08 / SEC-003): digits only, so "1e3", "+5" and "5.0" are rejected.
    return StrictIntegerField(
        min_value=1,
        max_value=MAX_QUANTITY,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
    )


def _token_field():
    # ESIMS-23: a fresh one-time token is generated every time a form is displayed.
    # required=False on purpose: other apps' tests (accounts/test_validation.py) build these forms
    # without a token. The VIEWS refuse a POST that has no token (see views._token_present).
    return forms.UUIDField(
        required=False,
        widget=forms.HiddenInput,
        initial=uuid.uuid4,
        error_messages={'invalid': TOKEN_ERROR},
    )


class StockInForm(forms.Form):
    product = ProductChoiceField(queryset=Product.objects.none(),
                                 widget=forms.Select(attrs={'class': 'form-select'}))
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.none(),
                                      widget=forms.Select(attrs={'class': 'form-select'}))
    quantity = _quantity_field()
    request_token = _token_field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only ACTIVE products/suppliers can be used in new transactions.
        self.fields['product'].queryset = Product.objects.filter(status=Product.Status.ACTIVE)
        self.fields['supplier'].queryset = Supplier.objects.filter(status=Supplier.Status.ACTIVE)


class StockOutForm(forms.Form):
    product = ProductChoiceField(queryset=Product.objects.none(),
                                 widget=forms.Select(attrs={'class': 'form-select'}))
    quantity = _quantity_field()
    request_token = _token_field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(status=Product.Status.ACTIVE)


class AuditFilterForm(forms.Form):
    """ESIMS-22: filters on the Administrator audit list (all optional, read from ?query=string)."""

    type = forms.ChoiceField(
        required=False,
        choices=[('', 'All types')] + list(StockTransaction.Type.choices),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    user = SanitizedCharField(
        required=False, max_length=150, label='User',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'username'}),
    )
    q = SanitizedCharField(
        required=False, max_length=100, label='Product or transaction ID',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'SKU, name or ID'}),
    )
    start = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control form-control-sm'}))
    end = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control form-control-sm'}))

    def clean(self):
        data = super().clean()
        start, end = data.get('start'), data.get('end')
        if start and end and start > end:
            raise forms.ValidationError('The start date must be on or before the end date.')
        return data
