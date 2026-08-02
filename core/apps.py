from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import models
import os


def create_default_superadmin(sender, **kwargs):
    """
    Ensures ONLY ONE Admin account exists on the platform:
    Name: Svathi
    Username: Svathi
    Password: svathi@2244
    Email: abhishekmutthalkar121@gmail.com
    No additional Admin accounts are permitted.
    """
    try:
        from django.contrib.auth.models import User
        from core.models import UserProfile

        admin_username = 'Svathi'
        admin_name = 'Svathi'
        admin_email = 'abhishekmutthalkar121@gmail.com'
        admin_password = 'svathi@2244'

        user = User.objects.filter(username__iexact=admin_username).first()
        if not user:
            user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name=admin_name
            )
        else:
            user.set_password(admin_password)
            user.email = admin_email
            user.first_name = admin_name
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'admin'
        profile.is_verified = True
        profile.is_suspended = False
        profile.save()

        # Demote any other users that might have is_staff=True or is_superuser=True or role='admin'
        other_staff = User.objects.exclude(pk=user.pk).filter(models.Q(is_staff=True) | models.Q(is_superuser=True))
        for other in other_staff:
            other.is_staff = False
            other.is_superuser = False
            other.save()

        UserProfile.objects.exclude(user=user).filter(role='admin').update(role='user')
    except Exception as e:
        pass


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        post_migrate.connect(create_default_superadmin, sender=self)

