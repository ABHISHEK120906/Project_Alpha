from django.apps import AppConfig


class SocialAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'social_auth'
    verbose_name = 'Social Authentication'

    def ready(self):
        # Ensure cleanup of expired OAuthState rows can be triggered at startup
        pass
