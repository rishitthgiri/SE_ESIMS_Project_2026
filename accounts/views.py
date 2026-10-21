from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render

from .forms import EmailOrUsernameAuthenticationForm


class ESIMSLoginView(LoginView):
    """ESIMS-02: login with username/email + password."""

    template_name = 'accounts/login.html'
    authentication_form = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')
