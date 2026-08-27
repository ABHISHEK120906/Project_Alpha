from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create default superusers for testing'

    def handle(self, *args, **options):
        users_to_create = [
            {
                'username': 'abhishek1234',
                'email': 'abhishekmutthalkar123@example.com',
                'password': 'team@1234',
            },
            {
                'username': 'abhishekmutthalkar',
                'email': 'abhishekmutthalkar@example.com',
                'password': 'team@1234',
            },
            {
                'username': 'abhishekmutthalkar@123',
                'email': 'abhishekmutthalkar@example.com',
                'password': 'team@1234',
            },
            {
                'username': 'Svathi',
                'email': 'svathi@example.com',
                'password': 'Abhishek@1296',
            },
        ]

        for udata in users_to_create:
            username = udata['username']
            password = udata['password']
            email = udata['email']

            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'is_staff': True, 'is_superuser': True}
            )

            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"Successfully created superuser '{username}'"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated superuser '{username}' password"))

