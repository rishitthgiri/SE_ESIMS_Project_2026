import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView

from accounts.mixins import AdminRequiredMixin

from . import services
from .forms import TOKEN_ERROR, AuditFilterForm, StockInForm, StockOutForm
from .models import StockTransaction


def _token_present(form):
    """ESIMS-23: every stock POST must carry its one-time form token. Adds an error if it is missing."""
    if form.cleaned_data.get('request_token') is None:
        form.add_error('request_token', TOKEN_ERROR)
        return False
    return True


def _duplicate_notice(request, existing):
    """ESIMS-23: a double-submit is not an error; show the transaction that was already saved."""
    messages.info(
        request,
        f'This transaction was already recorded (ID: {existing.transaction_id}). It was not saved twice.',
    )
    return redirect('transactions:list')


@login_required
@require_http_methods(['GET', 'POST'])
def stock_in(request):
    """ESIMS-18: Staff/Admin records a purchase against a registered supplier."""
    form = StockInForm(request.POST) if request.method == 'POST' else StockInForm()
    if request.method == 'POST' and form.is_valid() and _token_present(form):
        try:
            txn = services.record_stock_in(
                product=form.cleaned_data['product'],
                supplier=form.cleaned_data['supplier'],
                quantity=form.cleaned_data['quantity'],
                user=request.user,
                request_token=form.cleaned_data['request_token'],
            )
        except services.DuplicateSubmission as dup:
            return _duplicate_notice(request, dup.transaction)
        except services.StockError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(
                request,
                f'Stock-in recorded. Transaction ID: {txn.transaction_id}. '
                f'{txn.product.name} stock is now {txn.product.quantity_in_stock}.',
            )
            return redirect('transactions:list')
    return render(request, 'transactions/stock_in.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def stock_out(request):
    """ESIMS-19/20: Staff/Admin records a sale. Over-sales are rejected."""
    form = StockOutForm(request.POST) if request.method == 'POST' else StockOutForm()
    if request.method == 'POST' and form.is_valid() and _token_present(form):
        try:
            txn = services.record_stock_out(
                product=form.cleaned_data['product'],
                quantity=form.cleaned_data['quantity'],
                user=request.user,
                request_token=form.cleaned_data['request_token'],
            )
        except services.DuplicateSubmission as dup:
            return _duplicate_notice(request, dup.transaction)
        except services.InsufficientStock as exc:
            form.add_error('quantity', str(exc))
        except services.StockError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(
                request,
                f'Stock-out recorded. Transaction ID: {txn.transaction_id}. '
                f'{txn.product.name} stock is now {txn.product.quantity_in_stock}.',
            )
            return redirect('transactions:list')
    return render(request, 'transactions/stock_out.html', {'form': form})


@login_required
def transaction_list(request):
    """ESIMS-21: list of transactions with their unique IDs.

    Staff see their own transactions; Administrators see all of them.
    (The full Administrator audit list is `AuditTrailView`, ESIMS-22.)
    """
    qs = StockTransaction.objects.select_related('product', 'supplier', 'user')
    if not request.user.is_admin_role:
        qs = qs.filter(user=request.user)
    txn_type = request.GET.get('type')
    if txn_type in StockTransaction.Type.values:
        qs = qs.filter(transaction_type=txn_type)
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'transactions/transaction_list.html', {'page': page, 'txn_type': txn_type})


class AuditTrailView(AdminRequiredMixin, ListView):
    """ESIMS-22 / FR-014: Administrator-only audit trail of EVERY stock transaction.

    Read-only by design: the page has no forms that change data, the model refuses edits and
    deletes, and the Django admin screen for transactions is read-only too.
    Logged-out visitors go to the login page; Staff get a 403 (logged as an unauthorized attempt).
    """

    template_name = 'transactions/audit_trail.html'
    context_object_name = 'transactions'
    paginate_by = 25
    http_method_names = ['get', 'head', 'options']   # no POST/PUT/DELETE: nothing can be changed here

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.filter_form = AuditFilterForm(request.GET)

    def get_queryset(self):
        qs = StockTransaction.objects.select_related('product', 'supplier', 'user')
        form = self.filter_form
        if not form.is_valid():
            return qs.none()          # bad filter input: show nothing (and the error), never a wrong list
        data = form.cleaned_data
        if data['type']:
            qs = qs.filter(transaction_type=data['type'])
        if data['user']:
            qs = qs.filter(user__username__icontains=data['user'])
        if data['q']:
            needle = Q(product__sku__icontains=data['q']) | Q(product__name__icontains=data['q'])
            try:
                needle |= Q(transaction_id=uuid.UUID(data['q']))
            except ValueError:
                pass
            qs = qs.filter(needle)
        if data['start']:
            qs = qs.filter(timestamp__date__gte=data['start'])
        if data['end']:
            qs = qs.filter(timestamp__date__lte=data['end'])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop('page', None)
        context['filter_form'] = self.filter_form
        context['querystring'] = params.urlencode()
        context['total'] = context['paginator'].count if context.get('paginator') else len(context['transactions'])
        return context
