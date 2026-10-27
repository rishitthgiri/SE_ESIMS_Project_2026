from django import forms

from .models import Supplier


class SupplierForm(forms.ModelForm):
    """ESIMS-27: add / edit a supplier. Status is changed only via 'disable'."""

    class Meta:
        model = Supplier
        fields = ['name', 'contact']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Supplier name is required.')
        clash = Supplier.objects.filter(name__iexact=name)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('A supplier with this name already exists.')
        return name
