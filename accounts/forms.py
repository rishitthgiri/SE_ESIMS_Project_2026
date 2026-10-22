from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or email',
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    error_messages = {
        'invalid_login': 'Invalid username/email or password.',
        'inactive': 'This account is deactivated.',
    }
