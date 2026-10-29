"""Shared input validation and sanitization helpers (ESIMS-08 / SEC-003).

Any app can reuse these so that every form validates input the same way:

    from esims.validation import SanitizedCharField, StrictIntegerField, StrictDecimalField

Rules:
* Text is sanitized BEFORE it is validated or saved: control characters (including
  NUL bytes) are removed, HTML tags are stripped, whitespace is collapsed.
* Numbers must be plain ASCII digits - no "1e3", "+5", "5.0", " 5 ", unicode digits.
* Passwords are never touched by these helpers (they must be stored exactly as typed).
"""
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

_CONTROL_CHARS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_WHITESPACE = re.compile(r'\s+')
_INTEGER_RE = re.compile(r'^[0-9]+$')
_DECIMAL_RE = re.compile(r'^[0-9]+(\.[0-9]+)?$')


def sanitize_text(value, *, multiline=False):
    """Return a cleaned copy of `value`. Never raises; returns '' for None."""
    if value is None:
        return ''
    text = unicodedata.normalize('NFKC', str(value))
    text = _CONTROL_CHARS.sub('', text)
    text = strip_tags(text)
    if multiline:
        lines = [_WHITESPACE.sub(' ', line).strip() for line in text.splitlines()]
        return '\n'.join(line for line in lines if line)
    return _WHITESPACE.sub(' ', text).strip()


def validate_person_name(value):
    """Names: letters plus space . ' - only; must start with a letter."""
    if not value:
        return
    if not value[0].isalpha() or not all(ch.isalpha() or ch in " .'-" for ch in value):
        raise ValidationError(
            "Use letters, spaces, apostrophes, hyphens and full stops only.",
            code='invalid_name',
        )


class SanitizedCharField(forms.CharField):
    """CharField that sanitizes input before running validators."""

    def __init__(self, *args, multiline=False, **kwargs):
        self.multiline = multiline
        kwargs.setdefault('strip', False)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in self.empty_values:
            return self.empty_value
        return super().to_python(sanitize_text(value, multiline=self.multiline))


class StrictIntegerField(forms.IntegerField):
    """Whole numbers only (ASCII digits). Rejects '1e3', '+5', '5.0', '1,000', ' 5 '."""

    default_error_messages = {'invalid': 'Enter a whole number (digits only).'}

    def to_python(self, value):
        if value in self.empty_values:
            return None
        text = str(value)
        if isinstance(value, bool) or not _INTEGER_RE.match(text):
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        return int(text)


class StrictDecimalField(forms.DecimalField):
    """Money-style numbers: digits with an optional decimal part. No signs, exponents, NaN, Infinity."""

    default_error_messages = {'invalid': 'Enter a valid number (digits and an optional decimal part).'}

    def to_python(self, value):
        if value in self.empty_values:
            return None
        text = str(value)
        if isinstance(value, bool) or not _DECIMAL_RE.match(text):
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        try:
            return Decimal(text)
        except InvalidOperation:
            raise ValidationError(self.error_messages['invalid'], code='invalid')
