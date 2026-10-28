from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from esims.validation import SanitizedCharField, validate_person_name

User = get_user_model()


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or email',
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    error_messages = {
        'invalid_login': 'Invalid username/email or password.',
        'inactive': 'This account is deactivated.',
    }


def _name_field(label):
    # ESIMS-08: names are sanitized (tags / control chars removed) and restricted to letters etc.
    return SanitizedCharField(
        label=label, max_length=150, required=False, validators=[validate_person_name],
    )


class _StaffCleanMixin:
    """Shared cleaning for create/edit: email is lower-cased and must be unique ignoring case
    (login looks emails up case-insensitively, so 'A@x.com' and 'a@x.com' must not co-exist)."""

    def _style_widgets(self):
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        clash = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email


class StaffCreateForm(_StaffCleanMixin, UserCreationForm):
    """Admin creates a Staff account (ESIMS-05)."""

    first_name = _name_field('First name')
    last_name = _name_field('Last name')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_widgets()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STAFF   # the form can only ever create Staff, never Administrators
        if commit:
            user.save()
        return user


class StaffEditForm(_StaffCleanMixin, forms.ModelForm):
    """Admin edits a Staff account (ESIMS-05)."""

    first_name = _name_field('First name')
    last_name = _name_field('Last name')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_widgets()

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        clash = User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('A user with that username already exists.')
        return username
