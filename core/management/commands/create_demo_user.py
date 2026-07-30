from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a default demo user and superuser for testing'

    def handle(self, *args, **options):
        username = 'admin'
        password = 'admin123'
        email = 'admin@example.com'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True}
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Successfully created demo user '{username}' with password '{password}'"))
        else:
            # Ensure password is reset to admin123 if user exists
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Demo user '{username}' already exists. Password updated to '{password}'"))
