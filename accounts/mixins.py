from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """ESIMS-04: only Administrators may access the view.

    Anonymous users -> redirected to login. Logged-in Staff -> 403 Forbidden.
    """

    def test_func(self):
        return self.request.user.is_admin_role
