from django.urls import path
from . import views

app_name = 'social_auth'

urlpatterns = [
    # ── OAuth Flow ──────────────────────────────────────────────────────────
    # Step 1: Redirect user to provider auth page
    path('auth/social/<str:provider>/init/',     views.oauth_initiate, name='oauth_initiate'),
    # Step 2: Provider redirects back here with code + state
    path('auth/social/<str:provider>/callback/', views.oauth_callback, name='oauth_callback'),
    # Error display
    path('auth/social/error/',                   views.oauth_error,    name='oauth_error'),

    # ── User Settings: Connected Accounts ───────────────────────────────────
    path('profile/connected-accounts/',
         views.connected_accounts,
         name='connected_accounts'),
    path('profile/connected-accounts/<str:provider>/disconnect/',
         views.disconnect_provider,
         name='disconnect_provider'),
]
