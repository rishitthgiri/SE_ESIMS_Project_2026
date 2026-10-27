from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render
from django.views.generic import ListView

from .forms import EmailOrUsernameAuthenticationForm
from reports.alerts import low_stock_products

from .mixins import AdminRequiredMixin

User = get_user_model()


class ESIMSLoginView(LoginView):
    """ESIMS-02: login with username/email + password."""

    template_name = 'accounts/login.html'
    authentication_form = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html', {'low_stock': low_stock_products()})


class StaffListView(AdminRequiredMixin, ListView):
    """Admin-only page (ESIMS-04 demonstrates role restriction on it)."""

    model = User
    template_name = 'accounts/staff_list.html'
    context_object_name = 'staff_members'

    def get_queryset(self):
        return User.objects.filter(role=User.Role.STAFF).order_by('username')
