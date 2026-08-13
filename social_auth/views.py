"""
social_auth/views.py

OAuth 2.0 views:
  oauth_initiate      — Build auth URL and redirect user to provider
  oauth_callback      — Handle provider redirect, exchange code, link/create user
  oauth_error         — Professional error display page
  connected_accounts  — Show linked providers for logged-in user
  disconnect_provider — Unlink a provider (POST)
"""

import logging

import requests as http_requests
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import OAuthLoginHistory, SocialAccount
from .providers import (
    ACTIVE_LOGIN_PROVIDERS,
    PROVIDERS,
    get_provider_config,
    is_provider_configured,
)
from .utils import (
    build_authorization_url,
    exchange_code_for_token,
    fetch_userinfo,
    get_or_create_social_user,
    log_oauth_attempt,
    normalize_userinfo,
    verify_state,
    get_avatar_url,
)

logger = logging.getLogger('social_auth')


# ─────────────────────────────────────────────────────────────────────────────
# 1. Initiate OAuth Flow
# ─────────────────────────────────────────────────────────────────────────────

def oauth_initiate(request, provider: str):
    """
    Step 1: Generate state + PKCE, build the provider authorization URL,
    and redirect the user's browser to it.
    """
    # Validate provider
    try:
        get_provider_config(provider)
    except ValueError:
        return _render_error(request, 'unknown_provider',
                             f"The social login provider '{provider}' is not supported.")

    # Ensure credentials are configured
    if not is_provider_configured(provider):
        logger.warning('OAuth initiate: provider %s not configured (missing env vars)', provider)
        return _render_error(
            request, 'not_configured',
            f"Social login with {PROVIDERS[provider]['name']} is not configured. "
            "Please contact the administrator."
        )

    # Ensure session exists so we can bind state to it
    if not request.session.session_key:
        request.session.create()

    next_url = request.GET.get('next', '/dashboard/')
    if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
        next_url = '/dashboard/'

    try:
        auth_url = build_authorization_url(provider, request, next_url)
    except Exception as exc:
        logger.exception('Failed to build authorization URL for %s: %s', provider, exc)
        return _render_error(request, 'build_url_error',
                             'Unable to start social login. Please try again.')

    return redirect(auth_url)


# ─────────────────────────────────────────────────────────────────────────────
# 2. OAuth Callback
# ─────────────────────────────────────────────────────────────────────────────

def oauth_callback(request, provider: str):
    """
    Step 2: Provider redirects back here with ?code=...&state=...
    We validate state, exchange code for token, fetch userinfo,
    link/create the Django user, and log them in.
    """
    # Provider error response (e.g. user denied access)
    error = request.GET.get('error')
    if error:
        error_desc = request.GET.get('error_description', 'Authentication was cancelled or denied.')
        log_oauth_attempt(provider, 'cancelled', request,
                          error_code=error, error_message=error_desc)
        return _render_error(
            request, error,
            error_desc,
            provider=provider,
        )

    # Validate provider
    try:
        get_provider_config(provider)
    except ValueError:
        return _render_error(request, 'unknown_provider', f"Unknown provider: {provider}")

    # Extract params
    code = request.GET.get('code', '').strip()
    state_str = request.GET.get('state', '').strip()

    if not code or not state_str:
        log_oauth_attempt(provider, 'failed', request,
                          error_code='missing_params',
                          error_message='Missing code or state parameter in callback.')
        return _render_error(request, 'missing_params',
                             'Invalid OAuth callback — missing required parameters.')

    # ── State validation (CSRF) ─────────────────────────────────────────────
    try:
        state_obj = verify_state(state_str, provider)
    except ValueError as exc:
        log_oauth_attempt(provider, 'failed', request,
                          error_code='invalid_state', error_message=str(exc))
        return _render_error(request, 'invalid_state', str(exc), provider=provider)

    code_verifier = state_obj.code_verifier
    next_url = state_obj.next_url or '/dashboard/'

    # Clean up the state record (one-time use)
    state_obj.delete()

    # ── Token Exchange ──────────────────────────────────────────────────────
    try:
        token_data = exchange_code_for_token(provider, code, request, code_verifier)
    except http_requests.HTTPError as exc:
        msg = f'Token exchange failed: {exc.response.status_code if exc.response else "no response"}'
        logger.error('OAuth callback token exchange error for %s: %s', provider, exc)
        log_oauth_attempt(provider, 'error', request,
                          error_code='token_exchange_failed', error_message=msg)
        return _render_error(request, 'token_exchange_failed',
                             'Could not verify your identity with the provider. Please try again.',
                             provider=provider)
    except Exception as exc:
        logger.exception('OAuth token exchange unexpected error for %s', provider)
        log_oauth_attempt(provider, 'error', request,
                          error_code='unexpected_error', error_message=str(exc))
        return _render_error(request, 'unexpected_error',
                             'An unexpected error occurred. Please try again.',
                             provider=provider)

    # Detect token errors returned in the JSON body (GitHub pattern)
    if 'error' in token_data:
        err = token_data.get('error', '')
        desc = token_data.get('error_description', 'Token error from provider.')
        log_oauth_attempt(provider, 'failed', request,
                          error_code=err, error_message=desc)
        return _render_error(request, err, desc, provider=provider)

    # ── Fetch Userinfo ──────────────────────────────────────────────────────
    try:
        raw_userinfo = fetch_userinfo(provider, token_data)
    except http_requests.HTTPError as exc:
        msg = f'Userinfo fetch failed: {exc}'
        logger.error('OAuth userinfo fetch error for %s: %s', provider, exc)
        log_oauth_attempt(provider, 'error', request,
                          error_code='userinfo_failed', error_message=msg)
        return _render_error(request, 'userinfo_failed',
                             'Could not retrieve your profile from the provider.',
                             provider=provider)
    except Exception as exc:
        logger.exception('OAuth userinfo unexpected error for %s', provider)
        return _render_error(request, 'unexpected_error',
                             'Could not retrieve your profile. Please try again.',
                             provider=provider)

    # ── Normalise ───────────────────────────────────────────────────────────
    try:
        userinfo = normalize_userinfo(provider, raw_userinfo)
    except Exception as exc:
        logger.exception('OAuth normalize error for %s', provider)
        return _render_error(request, 'normalize_error',
                             'Could not process your profile data.',
                             provider=provider)

    if not userinfo.get('provider_user_id'):
        log_oauth_attempt(provider, 'failed', request,
                          error_code='missing_user_id',
                          error_message='Provider did not return a user identifier.')
        return _render_error(request, 'missing_user_id',
                             'The provider did not return a valid user identifier.',
                             provider=provider)

    # ── Get or Create User ──────────────────────────────────────────────────
    try:
        user, is_new = get_or_create_social_user(userinfo, provider, token_data, request)
    except Exception as exc:
        logger.exception('OAuth get_or_create_social_user error for %s', provider)
        log_oauth_attempt(provider, 'error', request,
                          error_code='user_create_failed', error_message=str(exc))
        return _render_error(request, 'user_create_failed',
                             'Unable to create or link your account. Please try again.',
                             provider=provider)

    # ── Login ───────────────────────────────────────────────────────────────
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    log_oauth_attempt(provider, 'success', request, user=user, is_new_account=is_new)

    provider_name = PROVIDERS.get(provider, {}).get('name', provider)
    if is_new:
        messages.success(
            request,
            f'🎉 Welcome to FreelanceTrack! Your account has been created via {provider_name}.'
        )
    else:
        messages.success(
            request,
            f'Welcome back! You signed in with {provider_name}.'
        )

    if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
        next_url = '/dashboard/'

    return redirect(next_url)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Error Page
# ─────────────────────────────────────────────────────────────────────────────

def oauth_error(request):
    """Render the generic OAuth error page."""
    error_code = request.GET.get('error', 'unknown')
    error_message = request.GET.get('message', 'An unknown error occurred.')
    provider = request.GET.get('provider', '')
    return render(request, 'social_auth/oauth_error.html', {
        'error_code': error_code,
        'error_message': error_message,
        'provider': provider,
        'provider_name': PROVIDERS.get(provider, {}).get('name', provider),
    })


def _render_error(request, error_code: str, message: str, provider: str = ''):
    """Internal helper: redirect to the OAuth error page."""
    import urllib.parse
    params = urllib.parse.urlencode({
        'error': error_code,
        'message': message,
        'provider': provider,
    })
    return redirect(f'/auth/social/error/?{params}')


# ─────────────────────────────────────────────────────────────────────────────
# 4. Connected Accounts (User Settings)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def connected_accounts(request):
    """
    Show the current user's linked social providers and recent OAuth login history.
    """
    linked = {
        sa.provider: sa
        for sa in SocialAccount.objects.filter(user=request.user, is_active=True)
    }

    provider_data = []
    for p in ACTIVE_LOGIN_PROVIDERS:
        cfg = PROVIDERS.get(p, {})
        social_acc = linked.get(p)
        provider_data.append({
            'key': p,
            'name': cfg.get('name', p),
            'color': cfg.get('color', '#666'),
            'is_linked': social_acc is not None,
            'social_account': social_acc,
            'is_configured': is_provider_configured(p),
            'avatar_url': get_avatar_url(
                social_acc.profile_photo_url if social_acc else None,
                social_acc.full_name if social_acc else '',
            ) if social_acc else None,
        })

    # Can the user disconnect? They must retain at least one login method.
    has_password = request.user.has_usable_password()
    linked_count = len(linked)

    oauth_history = OAuthLoginHistory.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:20]

    return render(request, 'social_auth/connected_accounts.html', {
        'provider_data': provider_data,
        'has_password': has_password,
        'linked_count': linked_count,
        'oauth_history': oauth_history,
        'can_disconnect': has_password or linked_count > 1,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 5. Disconnect Provider
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def disconnect_provider(request, provider: str):
    """
    Unlink a social provider from the current user's account.
    Safety check: user must have a usable password OR another linked provider.
    """
    try:
        social_account = SocialAccount.objects.get(
            user=request.user,
            provider=provider,
            is_active=True,
        )
    except SocialAccount.DoesNotExist:
        messages.warning(request, f'No linked {provider} account found.')
        return redirect('social_auth:connected_accounts')

    has_password = request.user.has_usable_password()
    other_linked = SocialAccount.objects.filter(
        user=request.user, is_active=True
    ).exclude(provider=provider).exists()

    if not has_password and not other_linked:
        messages.error(
            request,
            'Cannot disconnect your only login method. '
            'Please set a password first before disconnecting.'
        )
        return redirect('social_auth:connected_accounts')

    social_account.is_active = False
    social_account.access_token = ''
    social_account.refresh_token = ''
    social_account.save()

    provider_name = PROVIDERS.get(provider, {}).get('name', provider)
    messages.success(request, f'Successfully disconnected your {provider_name} account.')
    logger.info('User %s disconnected provider %s', request.user.username, provider)
    return redirect('social_auth:connected_accounts')
