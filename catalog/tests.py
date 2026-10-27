from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category

User = get_user_model()
PASSWORD = 'Pass@12345'


class CategoryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin1', 'admin1@esims.local', PASSWORD, role='ADMIN')
        self.staff = User.objects.create_user(
            'staff1', 'staff1@esims.local', PASSWORD, role='STAFF')

    def test_admin_can_add_category(self):
        self.client.login(username='admin1', password=PASSWORD)
        r = self.client.post(reverse('catalog:category_add'),
                             {'name': 'Mobiles', 'status': 'active'})
        self.assertRedirects(r, reverse('catalog:category_list'))
        self.assertTrue(Category.objects.filter(name='Mobiles').exists())

    def test_duplicate_name_rejected(self):
        Category.objects.create(name='Mobiles')
        self.client.login(username='admin1', password=PASSWORD)
        self.client.post(reverse('catalog:category_add'),
                         {'name': 'mobiles', 'status': 'active'})
        self.assertEqual(Category.objects.count(), 1)

    def test_blank_name_rejected(self):
        self.client.login(username='admin1', password=PASSWORD)
        self.client.post(reverse('catalog:category_add'),
                         {'name': '  ', 'status': 'active'})
        self.assertEqual(Category.objects.count(), 0)

    def test_edit_can_disable(self):
        c = Category.objects.create(name='Audio')
        self.client.login(username='admin1', password=PASSWORD)
        self.client.post(reverse('catalog:category_edit', args=[c.pk]),
                         {'name': 'Audio', 'status': 'disabled'})
        c.refresh_from_db()
        self.assertEqual(c.status, 'disabled')

    def test_staff_blocked(self):
        self.client.login(username='staff1', password=PASSWORD)
        r = self.client.post(reverse('catalog:category_add'),
                             {'name': 'Mobiles', 'status': 'active'})
        self.assertIn(r.status_code, (302, 403))
        self.assertEqual(Category.objects.count(), 0)

    def test_anonymous_redirected_to_login(self):
        r = self.client.get(reverse('catalog:category_list'))
        self.assertEqual(r.status_code, 302)
