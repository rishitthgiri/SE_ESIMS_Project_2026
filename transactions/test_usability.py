"""ESIMS-24: a stock transaction takes 4 screens or fewer (NFR-003, ST-USE-01).

"Screens" are counted from the dashboard (the page every user lands on after login):
    1. Dashboard  ->  2. Stock form  ->  3. Result page (transaction ID shown)
Run: python manage.py test transactions.test_usability -v 2
"""
from django.urls import reverse

from .models import StockTransaction
from .testutils import StockTestBase

MAX_SCREENS = 4


class FewScreensTests(StockTestBase):
    def setUp(self):
        self.client.force_login(self.staff)

    def walk(self, form_name, data):
        """Walk dashboard -> form -> submit. Returns the list of screens (page loads) seen by the user."""
        screens = []
        dashboard = self.client.get(reverse('accounts:dashboard'))
        screens.append(('dashboard', dashboard.status_code))
        # the menu link to the form must be on the dashboard (otherwise the user needs extra steps)
        self.assertContains(dashboard, f'href="{reverse(form_name)}"')

        form_page = self.client.get(reverse(form_name))
        screens.append(('form', form_page.status_code))
        data = dict(data, request_token=form_page.context['form']['request_token'].value())

        result = self.client.post(reverse(form_name), data, follow=True)
        screens.append(('result', result.status_code))
        self.assertEqual(len(result.redirect_chain), 1)          # one redirect, no hidden extra page
        return screens, result

    def test_stock_in_takes_three_screens(self):
        """ST-USE-01 / NFR-003"""
        screens, result = self.walk('transactions:stock_in',
                                    {'product': self.product.pk, 'supplier': self.supplier.pk, 'quantity': 3})
        self.assertLessEqual(len(screens), MAX_SCREENS)
        self.assertEqual(len(screens), 3)
        self.assertTrue(all(code == 200 for _, code in screens))
        self.assertContains(result, 'Stock-in recorded')
        self.assertContains(result, str(StockTransaction.objects.get().transaction_id))

    def test_stock_out_takes_three_screens(self):
        """ST-USE-01 / NFR-003"""
        screens, result = self.walk('transactions:stock_out', {'product': self.product.pk, 'quantity': 2})
        self.assertLessEqual(len(screens), MAX_SCREENS)
        self.assertEqual(len(screens), 3)
        self.assertTrue(all(code == 200 for _, code in screens))
        self.assertContains(result, 'Stock-out recorded')

    def test_forms_only_ask_for_what_is_needed(self):
        stock_in = self.client.get(reverse('transactions:stock_in')).context['form']
        stock_out = self.client.get(reverse('transactions:stock_out')).context['form']
        self.assertEqual([f.name for f in stock_in.visible_fields()], ['product', 'supplier', 'quantity'])
        self.assertEqual([f.name for f in stock_out.visible_fields()], ['product', 'quantity'])

    def test_a_rejected_sale_keeps_the_user_on_the_same_screen(self):
        """An error must not add extra screens: the form is shown again with the message"""
        form_page = self.client.get(reverse('transactions:stock_out'))
        token = form_page.context['form']['request_token'].value()
        resp = self.client.post(reverse('transactions:stock_out'),
                                {'product': self.product.pk, 'quantity': 6, 'request_token': token})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain if hasattr(resp, 'redirect_chain') else [], [])
        self.assertContains(resp, 'Only 5 unit(s)')
        self.assertContains(resp, 'name="quantity"')             # fix it right here and resubmit

    def test_every_page_has_stock_links_in_the_menu(self):
        for name in ('accounts:dashboard', 'transactions:list', 'transactions:stock_in', 'reports:low_stock'):
            body = self.client.get(reverse(name)).content.decode()
            self.assertIn(f'href="{reverse("transactions:stock_in")}"', body, name)
            self.assertIn(f'href="{reverse("transactions:stock_out")}"', body, name)
