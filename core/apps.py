from django.apps import AppConfig
from django.db.models.signals import post_migrate
import os


def create_default_superadmin(sender, **kwargs):
    """
    FEATURE 2 — Default Super Admin Auto-Initialization:
    Creates default superadmin account if non-existent during app initialization.
    Credentials: abhishekmutthalkar121@gmail.com / pagal@123
    """
    try:
        from django.contrib.auth.models import User
        from core.models import UserProfile

        admin_email = os.environ.get('DEFAULT_SUPERADMIN_EMAIL', 'abhishekmutthalkar121@gmail.com')
        admin_password = os.environ.get('DEFAULT_SUPERADMIN_PASSWORD', 'pagal@123')
        username = admin_email.split('@')[0]

        user = User.objects.filter(email=admin_email).first()
        if not user:
            user = User.objects.filter(username=username).first()

        if not user:
            user = User.objects.create_superuser(
                username=username,
                email=admin_email,
                password=admin_password
            )
        else:
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.role != 'admin':
            profile.role = 'admin'
            profile.is_verified = True
            profile.is_suspended = False
            profile.save()
    except Exception as e:
        pass


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        post_migrate.connect(create_default_superadmin, sender=self)

