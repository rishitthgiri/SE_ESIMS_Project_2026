from datetime import timedelta

from django import forms
from django.utils import timezone


class DateRangeForm(forms.Form):
    """Start / end date (both inclusive). Blank means "no limit" on that side."""

    start = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    end = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    def clean(self):
        data = super().clean()
        start, end = data.get('start'), data.get('end')
        if start and end and start > end:
            raise forms.ValidationError('The start date must be on or before the end date.')
        return data

    @classmethod
    def from_request(cls, request, default_days=None):
        """Bound form from ?start=&end=. With no dates at all, optionally default to the last N days."""
        params = request.GET
        if default_days and not (params.get('start') or params.get('end')) and 'start' not in params:
            today = timezone.localdate()
            return cls({'start': today - timedelta(days=default_days), 'end': today})
        return cls(params)
