"""Create one demo login for every kind of user ESIMS has.

    python manage.py seed_demo_users            # create any that are missing (safe to re-run)
    python manage.py seed_demo_users --reset    # also reset passwords/roles/flags of existing demo users
    python manage.py seed_demo_users --force    # allow running when DEBUG is off (never do this in production)

DEMO ONLY: these accounts use publicly documented passwords. Override with the
environment variable ESIMS_SEED_PASSWORD to use one password for all of them.
"""
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()

DEFAULT_PASSWORDS = {User.Role.ADMIN: 'Admin@12345', User.Role.STAFF: 'Staff@12345'}

DEMO_USERS = [
    # username, email, first, last, role, is_superuser, is_active, what it is for
    ('admin', 'admin@esims.local', 'Asha', 'Admin', User.Role.ADMIN, True, True,
     'Administrator + Django superuser (can also open /admin/)'),
    ('manager', 'manager@esims.local', 'Mohan', 'Manager', User.Role.ADMIN, False, True,
     'Administrator role only (no superuser) - proves role checks work on their own'),
    ('staff1', 'staff1@esims.local', 'Sneha', 'Staff', User.Role.STAFF, False, True,
     'Staff - day-to-day user'),
    ('staff2', 'staff2@esims.local', 'Sunil', 'Staff', User.Role.STAFF, False, True,
     'Staff - second user (to test "my own transactions" views)'),
    ('inactive_staff', 'inactive@esims.local', 'Ishaan', 'Inactive', User.Role.STAFF, False, False,
     'Deactivated Staff - login must be refused'),
]


class Command(BaseCommand):
    help = 'Create demo users covering every ESIMS role (Administrator, Staff, deactivated). DEMO ONLY.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Reset password, role and flags of demo users that already exist.')
        parser.add_argument('--force', action='store_true',
                            help='Allow running even when DEBUG is off.')

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['force']:
            raise CommandError('Refusing to create demo users while DEBUG is off. '
                               'Use --force only if you really mean it (never in production).')

        override = os.environ.get('ESIMS_SEED_PASSWORD')
        rows = []
        for username, email, first, last, role, superuser, active, purpose in DEMO_USERS:
            password = override or DEFAULT_PASSWORDS[role]
            user = User.objects.filter(username=username).first()
            if user is None:
                if User.objects.filter(email__iexact=email).exists():
                    self.stdout.write(self.style.WARNING(
                        f'{username}: skipped, email {email} already belongs to another user'))
                    continue
                user = User(username=username, email=email)
                status = 'created'
            elif options['reset']:
                status = 'reset'
            else:
                rows.append((username, '(unchanged)', role, 'exists - skipped', purpose))
                continue

            user.first_name, user.last_name = first, last
            user.role = role
            user.is_superuser = superuser
            user.is_staff = superuser          # only the superuser may open the Django /admin/ site
            user.is_active = active
            user.set_password(password)        # always stored hashed (PBKDF2)
            user.save()
            rows.append((username, password, role, status, purpose))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('ESIMS demo users (DEMO ONLY - do not use in production)'))
        self.stdout.write(f'{"username":<16}{"password":<16}{"role":<8}{"result":<17}purpose')
        for username, password, role, status, purpose in rows:
            self.stdout.write(f'{username:<16}{password:<16}{role:<8}{status:<17}{purpose}')
        self.stdout.write('')
