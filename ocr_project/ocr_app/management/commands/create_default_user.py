# management/commands/create_default_user.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create default admin user'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                password='admin123',
                email='admin@company.com',
                MUST_CHANGE_PASSWORD=True
            )
            self.stdout.write(self.style.SUCCESS('Default admin user created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))