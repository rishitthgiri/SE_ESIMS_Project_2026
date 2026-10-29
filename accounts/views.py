from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.defaults import permission_denied as default_permission_denied
from django.views.generic import CreateView, ListView, UpdateView

from reports.alerts import low_stock_products

from .forms import EmailOrUsernameAuthenticationForm, StaffCreateForm, StaffEditForm
from .mixins import AdminRequiredMixin
from .models import SecurityEvent
from .security import log_security_event

User = get_user_model()


class ESIMSLoginView(LoginView):
    """ESIMS-02: login with username/email + password."""

    template_name = 'accounts/login.html'
    authentication_form = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        # Wrong passwords are already logged by the user_login_failed signal. Input that the
        # form rejects BEFORE authentication (null bytes, absurdly long usernames) never reaches
        # that signal, so log it here - those are exactly the hostile attempts worth reviewing.
        raw = self.request.POST.get('username', '')
        if raw and 'username' in form.errors:
            log_security_event(
                SecurityEvent.EventType.LOGIN_FAILED, self.request,
                username=raw[:1000], details='Login input rejected by validation',
            )
        return super().form_invalid(form)


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html', {'low_stock': low_stock_products()})


def permission_denied(request, exception=None):
    """ESIMS-09: custom 403 handler (wired up as handler403 in esims/urls.py).

    Any PermissionDenied raised anywhere in the project ends up here, so unauthorized
    access attempts are logged no matter which app's view blocked them.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        user = None
    role = getattr(user, 'role', 'anonymous')
    log_security_event(
        SecurityEvent.EventType.UNAUTHORIZED_ACCESS, request,
        user=user, details=f'Access denied (role: {role})',
    )
    return default_permission_denied(request, exception)


# ---------------------------------------------------------------- ESIMS-04 / ESIMS-05
class StaffListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/staff_list.html'
    context_object_name = 'staff_members'

    def get_queryset(self):
        return User.objects.filter(role=User.Role.STAFF).order_by('username')


class StaffCreateView(AdminRequiredMixin, CreateView):
    form_class = StaffCreateForm
    template_name = 'accounts/staff_form.html'
    success_url = reverse_lazy('accounts:staff_list')

    def form_valid(self, form):
        messages.success(self.request, 'Staff account created.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Create Staff Account'
        return ctx


class StaffUpdateView(AdminRequiredMixin, UpdateView):
    form_class = StaffEditForm
    template_name = 'accounts/staff_form.html'
    success_url = reverse_lazy('accounts:staff_list')

    def get_queryset(self):
        return User.objects.filter(role=User.Role.STAFF)

    def form_valid(self, form):
        messages.success(self.request, 'Staff account updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Staff Account'
        return ctx


class StaffToggleActiveView(AdminRequiredMixin, View):
    """Deactivate / reactivate a Staff account (POST only, CSRF protected)."""

    http_method_names = ['post']

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, role=User.Role.STAFF)
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        state = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'Account "{user.username}" {state}.')
        return redirect('accounts:staff_list')


# ---------------------------------------------------------------- ESIMS-09
class SecurityLogView(AdminRequiredMixin, ListView):
    """Administrators review failed logins and unauthorized access attempts."""

    model = SecurityEvent
    template_name = 'accounts/security_log.html'
    context_object_name = 'events'
    paginate_by = 25

    def get_queryset(self):
        qs = SecurityEvent.objects.select_related('user')
        self.event_type = self.request.GET.get('type')
        if self.event_type in SecurityEvent.EventType.values:
            qs = qs.filter(event_type=self.event_type)
        else:
            self.event_type = None
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['event_type'] = self.event_type
        ctx['event_types'] = SecurityEvent.EventType.choices
        return ctx