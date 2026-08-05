from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create additional Super Admin accounts (Aparna, Astha, Anushri) without touching existing admins'

    def handle(self, *args, **options):
        admins_to_create = [
            {
                'username': 'Aparna',
                'first_name': 'Aparna',
                'email': 'aparna@admin.local',
                'password': 'aparna@6226',
            },
            {
                'username': 'Astha',
                'first_name': 'Astha',
                'email': 'astha@admin.local',
                'password': 'astha@1221',
            },
            {
                'username': 'Anushri',
                'first_name': 'Anushri',
                'email': 'anushri@admin.local',
                'password': 'anushri@9988',
            },
        ]

        for admin_data in admins_to_create:
            username = admin_data['username']
            email = admin_data['email']
            password = admin_data['password']
            first_name = admin_data['first_name']

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )

            # Always ensure these flags are set (in case account already existed)
            user.first_name = first_name
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[CREATED] Super Admin '{username}' ({email})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"[UPDATED] Super Admin '{username}' already existed — updated to Super Admin privileges."
                    )
                )

        self.stdout.write(self.style.SUCCESS('\nAll three admin accounts are ready.'))
