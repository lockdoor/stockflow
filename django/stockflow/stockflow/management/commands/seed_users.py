from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Seed initial users (admin, staff)"

    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true', help='Delete existing users first')

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write("🧹 Deleting all users except superusers...")
            User.objects.exclude(is_superuser=True).delete()

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS("✅ Created superuser 'admin'"))

        # Staff user
        if not User.objects.filter(username='staff').exists():
            User.objects.create_user(
                username='staff',
                email='staff@example.com',
                password='staff123',
                is_staff=True
            )
            self.stdout.write(self.style.SUCCESS("✅ Created staff user 'staff'"))
