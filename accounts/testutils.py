"""Small helpers shared by the Sprint 2 test modules."""
from django.contrib.auth import get_user_model

User = get_user_model()
PASSWORD = 'Pass@12345'


def make_user(username='staff1', password=PASSWORD, role=None, **extra):
    role = role or User.Role.STAFF
    extra.setdefault('email', f'{username}@esims.local')
    return User.objects.create_user(username=username, password=password, role=role, **extra)


def make_admin(username='admin1', **extra):
    return make_user(username, role=User.Role.ADMIN, **extra)
