"""
social_auth/utils.py

Core OAuth flow utilities:
  - PKCE pair generation
  - State creation / validation
  - Authorization URL building
  - Token exchange (code → access_token)
  - Userinfo fetching and normalisation (provider-specific → standard dict)
  - Account linking / user creation (no duplicate users)
  - IP extraction helper
  - Redirect URI builder
"""

import base64
import hashlib
import logging
import os
import secrets
import urllib.parse
from datetime import timedelta

import requests as http_requests
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import OAuthState, OAuthLoginHistory, SocialAccount
from .providers import get_provider_config, get_client_id, get_client_secret

logger = logging.getLogger('social_auth')

# ─────────────────────────────────────────────────────────────────────────────
# PKCE (RFC 7636)
# ─────────────────────────────────────────────────────────────────────────────

def generate_pkce_pair():
    """
    Generate a (code_verifier, code_challenge) PKCE pair.
    code_verifier: 96-byte URL-safe random string
    code_challenge: S256 hash → base64url without padding
    """
    code_verifier = secrets.token_urlsafe(72)  # 96 url-safe chars
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return code_verifier, code_challenge


# ─────────────────────────────────────────────────────────────────────────────
# OAuth State (CSRF protection)
# ─────────────────────────────────────────────────────────────────────────────

def generate_state(provider: str, request, next_url: str = '') -> tuple:
    """
    Create a cryptographically random state token, persist it in DB,
    and return (state, code_verifier_or_None).
    Expires in 10 minutes.
    """
    # Clean up expired states older than 15 minutes
    OAuthState.objects.filter(expires_at__lt=timezone.now()).delete()

    state = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(minutes=10)

    cfg = get_provider_config(provider)
    code_verifier = None
    if cfg.get('pkce'):
        code_verifier, _ = generate_pkce_pair()

    OAuthState.objects.create(
        state=state,
        provider=provider,
        code_verifier=code_verifier,
        next_url=next_url or '/dashboard/',
        session_key=request.session.session_key,
        expires_at=expires_at,
    )
    return state, code_verifier


def verify_state(state_str: str, provider: str) -> OAuthState:
    """
    Validate and return the OAuthState object.
    Raises ValueError on invalid, expired, or provider-mismatch.
    """
    try:
        state_obj = OAuthState.objects.get(state=state_str, provider=provider)
    except OAuthState.DoesNotExist:
        raise ValueError('Invalid or unknown OAuth state parameter.')

    if not state_obj.is_valid():
        state_obj.delete()
        raise ValueError('OAuth state has expired. Please try again.')

    return state_obj


# ─────────────────────────────────────────────────────────────────────────────
# Redirect URI
# ─────────────────────────────────────────────────────────────────────────────

def get_redirect_uri(request, provider: str) -> str:
    """Build the absolute OAuth callback URL for this provider."""
    base = os.environ.get(
        'SOCIAL_AUTH_CALLBACK_BASE_URL',
        request.build_absolute_uri('/')[:-1]   # e.g. https://example.com
    )
    path = reverse('social_auth:oauth_callback', kwargs={'provider': provider})
    return f'{base}{path}'


# ─────────────────────────────────────────────────────────────────────────────
# Authorization URL builder
# ─────────────────────────────────────────────────────────────────────────────

def build_authorization_url(provider: str, request, next_url: str = '') -> str:
    """
    Return the full provider authorization URL including all OAuth params,
    state, PKCE challenge (if applicable), and scopes.
    """
    cfg = get_provider_config(provider)
    client_id = get_client_id(provider)

    state, code_verifier = generate_state(provider, request, next_url)
    redirect_uri = get_redirect_uri(request, provider)

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': cfg['scope'],
        'state': state,
    }

    # PKCE challenge
    if cfg.get('pkce') and code_verifier:
        digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
        params['code_challenge'] = code_challenge
        params['code_challenge_method'] = 'S256'

    # Provider-specific extra params
    params.update(cfg.get('extra_params', {}))

    return cfg['auth_url'] + '?' + urllib.parse.urlencode(params)


# ─────────────────────────────────────────────────────────────────────────────
# Token Exchange
# ─────────────────────────────────────────────────────────────────────────────

def exchange_code_for_token(provider: str, code: str, request, code_verifier=None) -> dict:
    """
    Exchange authorization code for access token.
    Returns the raw token response dict.
    Raises requests.HTTPError on failure.
    """
    cfg = get_provider_config(provider)
    redirect_uri = get_redirect_uri(request, provider)

    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': get_client_id(provider),
    }

    # PKCE providers send code_verifier instead of client_secret (or in addition)
    if code_verifier:
        payload['code_verifier'] = code_verifier

    # Twitter v2 uses Basic Auth for client credentials
    if provider == 'twitter':
        auth = (get_client_id(provider), get_client_secret(provider))
        response = http_requests.post(
            cfg['token_url'],
            data=payload,
            auth=auth,
            timeout=15,
        )
    else:
        payload['client_secret'] = get_client_secret(provider)
        headers = {}
        if provider == 'github':
            headers['Accept'] = 'application/json'
        response = http_requests.post(
            cfg['token_url'],
            data=payload,
            headers=headers,
            timeout=15,
        )

    response.raise_for_status()

    if provider == 'github':
        # GitHub returns form-encoded by default unless Accept: application/json
        try:
            return response.json()
        except Exception:
            return dict(urllib.parse.parse_qsl(response.text))

    return response.json()


# ─────────────────────────────────────────────────────────────────────────────
# Userinfo Fetching
# ─────────────────────────────────────────────────────────────────────────────

def fetch_userinfo(provider: str, token_data: dict) -> dict:
    """
    Fetch raw user profile data from the provider's userinfo endpoint.
    Returns raw response dict from provider.
    """
    cfg = get_provider_config(provider)
    access_token = token_data.get('access_token', '')
    headers = {'Authorization': f'Bearer {access_token}'}

    if provider == 'github':
        # Fetch base profile
        r = http_requests.get(cfg['userinfo_url'], headers=headers, timeout=15)
        r.raise_for_status()
        profile = r.json()

        # GitHub may return null email; fetch from /user/emails endpoint
        if not profile.get('email'):
            email_r = http_requests.get(
                cfg.get('email_url', 'https://api.github.com/user/emails'),
                headers=headers, timeout=15
            )
            if email_r.status_code == 200:
                emails = email_r.json()
                primary = next(
                    (e['email'] for e in emails if e.get('primary') and e.get('verified')),
                    None
                )
                if primary:
                    profile['email'] = primary
        return profile

    if provider == 'reddit':
        # Reddit API uses bearer token differently
        headers['User-Agent'] = 'FreelanceTrack/1.0'
        r = http_requests.get(cfg['userinfo_url'], headers=headers, timeout=15)
    else:
        r = http_requests.get(cfg['userinfo_url'], headers=headers, timeout=15)

    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# Userinfo Normalisation
# ─────────────────────────────────────────────────────────────────────────────

def normalize_userinfo(provider: str, raw: dict) -> dict:
    """
    Convert provider-specific userinfo dict into a standard internal dict:
    {
        provider_user_id: str,
        email: str | None,
        full_name: str,
        profile_photo_url: str | None,
        is_verified: bool,
    }
    """
    if provider == 'google':
        return {
            'provider_user_id': str(raw.get('sub', '')),
            'email': raw.get('email'),
            'full_name': raw.get('name', ''),
            'profile_photo_url': raw.get('picture'),
            'is_verified': raw.get('email_verified', False),
        }

    elif provider == 'github':
        return {
            'provider_user_id': str(raw.get('id', '')),
            'email': raw.get('email'),
            'full_name': raw.get('name') or raw.get('login', ''),
            'profile_photo_url': raw.get('avatar_url'),
            'is_verified': bool(raw.get('email')),  # GitHub only returns verified emails
        }

    elif provider == 'linkedin':
        # OpenID Connect endpoint returns standard claims
        return {
            'provider_user_id': str(raw.get('sub', '')),
            'email': raw.get('email'),
            'full_name': raw.get('name', f"{raw.get('given_name','')} {raw.get('family_name','')}".strip()),
            'profile_photo_url': raw.get('picture'),
            'is_verified': raw.get('email_verified', False),
        }

    elif provider == 'microsoft':
        return {
            'provider_user_id': str(raw.get('id', '')),
            'email': raw.get('mail') or raw.get('userPrincipalName'),
            'full_name': raw.get('displayName', ''),
            'profile_photo_url': None,  # Separate Graph API call needed for photo
            'is_verified': True,  # Microsoft accounts are verified
        }

    elif provider == 'facebook':
        photo = None
        if raw.get('picture', {}).get('data', {}).get('url'):
            photo = raw['picture']['data']['url']
        return {
            'provider_user_id': str(raw.get('id', '')),
            'email': raw.get('email'),
            'full_name': raw.get('name', ''),
            'profile_photo_url': photo,
            'is_verified': bool(raw.get('email')),
        }

    elif provider == 'twitter':
        user_data = raw.get('data', raw)
        return {
            'provider_user_id': str(user_data.get('id', '')),
            'email': user_data.get('email'),   # Requires elevated access
            'full_name': user_data.get('name', user_data.get('username', '')),
            'profile_photo_url': user_data.get('profile_image_url', '').replace('_normal', '_400x400') or None,
            'is_verified': False,  # Twitter email requires elevated access
        }

    else:
        # Generic OpenID Connect fallback
        return {
            'provider_user_id': str(raw.get('sub') or raw.get('id', '')),
            'email': raw.get('email'),
            'full_name': raw.get('name', ''),
            'profile_photo_url': raw.get('picture') or raw.get('avatar_url'),
            'is_verified': raw.get('email_verified', False),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Account Linking / User Creation (core business logic)
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_social_user(userinfo: dict, provider: str, token_data: dict, request):
    """
    The heart of the social auth system.

    Priority order:
      1. Existing SocialAccount (same provider + provider_user_id)  → return linked user
      2. Existing Django User with same email                        → link provider, return user
      3. No match                                                    → create new User + Profile + SocialAccount

    Returns (user, is_new_account: bool)
    Never creates duplicate users.
    """
    from core.models import UserProfile   # imported here to avoid circular import

    provider_user_id = userinfo['provider_user_id']
    email = (userinfo.get('email') or '').strip().lower() or None
    full_name = userinfo.get('full_name', '')
    profile_photo_url = userinfo.get('profile_photo_url')
    is_verified = userinfo.get('is_verified', False)
    is_new_account = False

    # ── Case 1: Existing SocialAccount ───────────────────────────────────────
    try:
        social_account = SocialAccount.objects.get(
            provider=provider,
            provider_user_id=provider_user_id,
        )
        # Refresh tokens and profile data
        social_account.access_token = token_data.get('access_token', '')
        social_account.refresh_token = token_data.get('refresh_token', '')
        if full_name:
            social_account.full_name = full_name
        if profile_photo_url:
            social_account.profile_photo_url = profile_photo_url
        social_account.update_last_login()   # also saves
        logger.info('Social login: existing account — user=%s provider=%s', social_account.user.username, provider)
        return social_account.user, is_new_account

    except SocialAccount.DoesNotExist:
        pass

    # ── Case 2: Match by email → link provider ────────────────────────────────
    user = None
    if email:
        user = User.objects.filter(email__iexact=email).first()

    if user:
        social_account, _ = SocialAccount.objects.get_or_create(
            provider=provider,
            provider_user_id=provider_user_id,
            defaults={'user': user},
        )
        social_account.user = user
        social_account.email = email
        social_account.full_name = full_name
        social_account.profile_photo_url = profile_photo_url
        social_account.access_token = token_data.get('access_token', '')
        social_account.refresh_token = token_data.get('refresh_token', '')
        social_account.is_verified = is_verified
        social_account.save()
        social_account.update_last_login()

        # If provider says email is verified, mark user profile verified too
        if is_verified:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if not profile.is_verified:
                profile.is_verified = True
                user.is_active = True
                user.save(update_fields=['is_active'])
                profile.save(update_fields=['is_verified'])

        logger.info('Social login: linked to existing user=%s provider=%s', user.username, provider)
        return user, is_new_account

    # ── Case 3: Create new User + Profile + SocialAccount ────────────────────
    is_new_account = True

    # Build a unique username from full_name or email
    base_username = _derive_username(full_name, email, provider)
    username = _unique_username(base_username)

    user = User.objects.create_user(
        username=username,
        email=email or '',
        password=None,   # unusable password — must login via social
    )
    if full_name:
        parts = full_name.split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''
    user.is_active = True   # social-authenticated users are active immediately
    user.save()

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.role = 'user'
    profile.is_verified = is_verified
    profile.save()

    SocialAccount.objects.create(
        user=user,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        full_name=full_name,
        profile_photo_url=profile_photo_url,
        access_token=token_data.get('access_token', ''),
        refresh_token=token_data.get('refresh_token', ''),
        is_verified=is_verified,
        last_login=timezone.now(),
    )

    logger.info('Social login: new account created user=%s provider=%s', username, provider)
    return user, is_new_account


# ─────────────────────────────────────────────────────────────────────────────
# Username helpers
# ─────────────────────────────────────────────────────────────────────────────

def _derive_username(full_name: str, email: str | None, provider: str) -> str:
    """Derive a clean base username from available data."""
    import re
    if full_name:
        slug = re.sub(r'[^a-z0-9]', '', full_name.lower().replace(' ', '_'))
        if slug:
            return slug[:28]
    if email:
        local = email.split('@')[0]
        slug = re.sub(r'[^a-z0-9_]', '', local.lower())
        if slug:
            return slug[:28]
    return provider + '_user'


def _unique_username(base: str) -> str:
    """Append a counter suffix until we find a username not in use."""
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{counter}'
        counter += 1
    return username


# ─────────────────────────────────────────────────────────────────────────────
# Audit Logging
# ─────────────────────────────────────────────────────────────────────────────

def log_oauth_attempt(provider: str, status: str, request, user=None,
                      error_code='', error_message='', is_new_account=False):
    """Write an OAuthLoginHistory record."""
    ip = get_client_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:512]
    OAuthLoginHistory.objects.create(
        user=user,
        provider=provider,
        status=status,
        ip_address=ip,
        user_agent=ua,
        error_code=error_code or '',
        error_message=error_message or '',
        is_new_account=is_new_account,
    )


def get_client_ip(request) -> str | None:
    """Extract the real client IP from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ─────────────────────────────────────────────────────────────────────────────
# Avatar fallback
# ─────────────────────────────────────────────────────────────────────────────

def get_avatar_url(profile_photo_url: str | None, full_name: str, size: int = 80) -> str:
    """Return photo URL if available, else a UI Avatars initials URL."""
    if profile_photo_url:
        return profile_photo_url
    name_param = urllib.parse.quote(full_name or '?')
    return f'https://ui-avatars.com/api/?name={name_param}&size={size}&background=DB9941&color=07111D&bold=true'
