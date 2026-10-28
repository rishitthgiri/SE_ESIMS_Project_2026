"""ESIMS-08 / SEC-003: input validation and sanitization (including negative tests)."""
from decimal import Decimal

from django import forms
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from catalog.models import Category, Product
from suppliers.models import Supplier
from transactions.forms import StockInForm, StockOutForm
from transactions.services import MAX_QUANTITY

from esims.validation import (
    SanitizedCharField, StrictDecimalField, StrictIntegerField, sanitize_text, validate_person_name,
)

from .forms import StaffCreateForm, StaffEditForm
from .testutils import PASSWORD, User, make_admin, make_user

STRONG = 'Str0ng@Pass99'


class SanitizeTextTests(SimpleTestCase):
    def test_none_becomes_empty(self):
        self.assertEqual(sanitize_text(None), '')

    def test_tags_are_stripped(self):
        self.assertEqual(sanitize_text('<b>Anna</b>'), 'Anna')
        self.assertNotIn('<', sanitize_text('<script>alert(1)</script>x'))

    def test_control_characters_and_nul_removed(self):
        self.assertEqual(sanitize_text('a\x00b\x07c\x1bd'), 'abcd')

    def test_whitespace_collapsed_and_trimmed(self):
        self.assertEqual(sanitize_text('  Anne \t  Marie \n '), 'Anne Marie')

    def test_unicode_is_normalized(self):
        self.assertEqual(sanitize_text('\uff21\uff22'), 'AB')   # full-width letters -> ascii

    def test_log_injection_newlines_removed_in_single_line_mode(self):
        self.assertNotIn('\n', sanitize_text('bob\nFAKE LOG LINE'))

    def test_multiline_mode_keeps_line_breaks(self):
        self.assertEqual(sanitize_text('a\n\n b ', multiline=True), 'a\nb')


class StrictIntegerFieldTests(SimpleTestCase):
    def field(self):
        return StrictIntegerField(min_value=1, max_value=100)

    def test_accepts_plain_digits(self):
        self.assertEqual(self.field().clean('42'), 42)

    def test_rejects_invalid_values(self):
        for bad in ('', 'abc', '1e3', '+5', '-1', '0', '5.0', '3.5', ' 5 ', '1,000', '0x10', '٣', '101', '9' * 30):
            with self.subTest(value=bad):
                with self.assertRaises(forms.ValidationError):
                    self.field().clean(bad)

    def test_rejects_bool(self):
        with self.assertRaises(forms.ValidationError):
            self.field().clean(True)


class StrictDecimalFieldTests(SimpleTestCase):
    def field(self):
        return StrictDecimalField(max_digits=10, decimal_places=2, min_value=0)

    def test_accepts_money_values(self):
        self.assertEqual(self.field().clean('19999.50'), Decimal('19999.50'))
        self.assertEqual(self.field().clean('0'), Decimal('0'))

    def test_rejects_invalid_values(self):
        for bad in ('', 'abc', 'NaN', 'Infinity', '-1', '+1', '1e2', '1.2.3', '10.505', '12345678901', ' 5', '1,5'):
            with self.subTest(value=bad):
                with self.assertRaises(forms.ValidationError):
                    self.field().clean(bad)


class PersonNameTests(SimpleTestCase):
    def test_valid_names(self):
        for ok in ("O'Brien", 'Anne-Marie', 'J. R. Tolkien', 'Zoë', ''):
            validate_person_name(ok)

    def test_invalid_names(self):
        for bad in ('alert(1)', 'Bob123', '-Bob', '"; DROP TABLE', 'a<b', '1st'):
            with self.subTest(name=bad):
                with self.assertRaises(forms.ValidationError):
                    validate_person_name(bad)


class SanitizedCharFieldTests(SimpleTestCase):
    def test_sanitizes_before_validating(self):
        f = SanitizedCharField(max_length=10)
        self.assertEqual(f.clean('  <i>Hi</i>  '), 'Hi')

    def test_required_empty_after_sanitizing_is_rejected(self):
        with self.assertRaises(forms.ValidationError):
            SanitizedCharField(max_length=10).clean('<b></b>   ')

    def test_max_length_enforced_after_sanitizing(self):
        with self.assertRaises(forms.ValidationError):
            SanitizedCharField(max_length=3).clean('abcdef')


def staff_data(**kw):
    d = {'username': 'newstaff', 'email': 'new@esims.local', 'first_name': 'New', 'last_name': 'Staff',
         'password1': STRONG, 'password2': STRONG}
    d.update(kw)
    return d


class StaffFormValidationTests(TestCase):
    def test_valid_form(self):
        self.assertTrue(StaffCreateForm(staff_data()).is_valid())

    def test_script_in_name_is_rejected(self):
        f = StaffCreateForm(staff_data(first_name='<script>alert(1)</script>Bob'))
        self.assertFalse(f.is_valid())
        self.assertIn('first_name', f.errors)

    def test_harmless_markup_in_name_is_stripped_not_stored(self):
        f = StaffCreateForm(staff_data(first_name='<b>Anna</b>'))
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['first_name'], 'Anna')

    def test_nul_byte_removed(self):
        f = StaffCreateForm(staff_data(first_name='Ann\x00a'))
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['first_name'], 'Anna')

    def test_name_too_long_rejected(self):
        self.assertFalse(StaffCreateForm(staff_data(last_name='a' * 151)).is_valid())

    def test_bad_email_rejected(self):
        for bad in ('', 'not-an-email', 'a@', '@b.com', 'a b@c.com'):
            with self.subTest(email=bad):
                self.assertFalse(StaffCreateForm(staff_data(email=bad)).is_valid())

    def test_bad_username_rejected(self):
        for bad in ('', 'has space', '<script>', 'a' * 151, "x'; --"):
            with self.subTest(username=bad):
                self.assertFalse(StaffCreateForm(staff_data(username=bad)).is_valid())

    def test_edit_form_rejects_script_in_name(self):
        u = make_user('s1')
        f = StaffEditForm({'username': 's1', 'email': 's1@esims.local', 'first_name': '<script>alert(1)</script>', 'last_name': ''},
                          instance=u)
        self.assertFalse(f.is_valid())


class LoginInputTests(TestCase):
    def setUp(self):
        make_user('staff1')

    def test_sql_injection_style_input_is_just_an_invalid_login(self):
        r = self.client.post(reverse('accounts:login'), {'username': "' OR '1'='1", 'password': "' OR '1'='1"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Invalid username/email or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_very_long_username_is_rejected_without_crashing(self):
        r = self.client.post(reverse('accounts:login'), {'username': 'a' * 5000, 'password': PASSWORD})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_empty_fields_rejected(self):
        r = self.client.post(reverse('accounts:login'), {'username': '', 'password': ''})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class StockQuantityValidationTests(TestCase):
    """Negative tests for the numeric fields on the stock forms (Samiksha's module)."""

    def setUp(self):
        cat = Category.objects.create(name='Phones')
        self.supplier = Supplier.objects.create(name='Acme')
        self.product = Product.objects.create(sku='P-1', name='Phone', category=cat, price='100.00', quantity_in_stock=5)

    def _out(self, qty):
        return StockOutForm({'product': self.product.pk, 'quantity': qty})

    def _in(self, qty):
        return StockInForm({'product': self.product.pk, 'supplier': self.supplier.pk, 'quantity': qty})

    BAD = ['', '0', '-1', '-5', 'abc', '1.5', '5.0', '+5', ' 5 ', '1e3', '1,000', '١٢', str(MAX_QUANTITY + 1), '9' * 40, '<script>']

    def test_stock_out_rejects_invalid_quantities(self):
        for bad in self.BAD:
            with self.subTest(quantity=bad):
                self.assertFalse(self._out(bad).is_valid())

    def test_stock_in_rejects_invalid_quantities(self):
        for bad in self.BAD:
            with self.subTest(quantity=bad):
                self.assertFalse(self._in(bad).is_valid())

    def test_valid_quantities_are_accepted(self):
        for ok in ('1', '5', str(MAX_QUANTITY)):
            with self.subTest(quantity=ok):
                self.assertTrue(self._in(ok).is_valid(), self._in(ok).errors)

    def test_invalid_quantity_never_changes_stock(self):
        make_user('staff1')
        self.client.login(username='staff1', password=PASSWORD)
        for bad in ('-3', 'abc', '1e3', '0'):
            self.client.post(reverse('transactions:stock_out'), {'product': self.product.pk, 'quantity': bad})
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 5)

    def test_unknown_or_malformed_product_id_rejected(self):
        for bad in ('not-a-uuid', '00000000-0000-0000-0000-000000000000', ''):
            with self.subTest(product=bad):
                self.assertFalse(StockOutForm({'product': bad, 'quantity': '1'}).is_valid())
