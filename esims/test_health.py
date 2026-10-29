from unittest import mock

from django.test import TestCase


class HealthTests(TestCase):
    def test_ok_without_login(self):
        r = self.client.get('/health/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'status': 'ok'})

    def test_database_down_gives_503(self):
        with mock.patch('esims.health.connection') as conn:
            conn.cursor.side_effect = Exception('db down')
            r = self.client.get('/health/')
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json(), {'status': 'error'})
        self.assertNotIn('db down', r.content.decode())
