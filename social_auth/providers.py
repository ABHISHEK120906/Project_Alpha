"""
social_auth/providers.py

Provider configuration registry.
Adding a new OAuth provider = add one dict entry here.
All credentials are loaded from environment variables — never hardcoded.
"""

import os

# ─────────────────────────────────────────────────────────────────────────────
# Each provider dict must contain:
#   name              Human-readable name
#   auth_url          Authorization endpoint
#   token_url         Token exchange endpoint
#   userinfo_url      User-info endpoint (or None if embedded in token)
#   scope             Space-separated OAuth scopes
#   pkce              Whether to use PKCE (RFC 7636)
#   extra_params      Extra URL params for auth_url (dict)
#   env_client_id     Env var name for client ID
#   env_client_secret Env var name for client secret (None for PKCE-only)
# ─────────────────────────────────────────────────────────────────────────────

PROVIDERS = {
    'google': {
        'name': 'Google',
        'color': '#ffffff',
        'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'userinfo_url': 'https://openidconnect.googleapis.com/v1/userinfo',
        'scope': 'openid email profile',
        'pkce': True,
        'extra_params': {
            'access_type': 'offline',
            'prompt': 'select_account',
        },
        'env_client_id': 'GOOGLE_CLIENT_ID',
        'env_client_secret': 'GOOGLE_CLIENT_SECRET',
    },

    'github': {
        'name': 'GitHub',
        'color': '#24292f',
        'auth_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo_url': 'https://api.github.com/user',
        'email_url': 'https://api.github.com/user/emails',  # GitHub-specific
        'scope': 'read:user user:email',
        'pkce': False,
        'extra_params': {},
        'env_client_id': 'GITHUB_CLIENT_ID',
        'env_client_secret': 'GITHUB_CLIENT_SECRET',
    },

    'linkedin': {
        'name': 'LinkedIn',
        'color': '#0a66c2',
        'auth_url': 'https://www.linkedin.com/oauth/v2/authorization',
        'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
        'userinfo_url': 'https://api.linkedin.com/v2/userinfo',   # OpenID Connect
        'scope': 'openid profile email',
        'pkce': False,
        'extra_params': {},
        'env_client_id': 'LINKEDIN_CLIENT_ID',
        'env_client_secret': 'LINKEDIN_CLIENT_SECRET',
    },

    'microsoft': {
        'name': 'Microsoft',
        'color': '#2f2f2f',
        'auth_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
        'scope': 'openid profile email User.Read',
        'pkce': True,
        'extra_params': {
            'response_mode': 'query',
        },
        'env_client_id': 'MICROSOFT_CLIENT_ID',
        'env_client_secret': 'MICROSOFT_CLIENT_SECRET',
    },

    'facebook': {
        'name': 'Facebook',
        'color': '#1877f2',
        'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
        'userinfo_url': 'https://graph.facebook.com/me?fields=id,name,email,picture.width(400)',
        'scope': 'email public_profile',
        'pkce': False,
        'extra_params': {
            'display': 'popup',
        },
        'env_client_id': 'FACEBOOK_CLIENT_ID',
        'env_client_secret': 'FACEBOOK_CLIENT_SECRET',
    },

    'twitter': {
        'name': 'X (Twitter)',
        'color': '#000000',
        'auth_url': 'https://twitter.com/i/oauth2/authorize',
        'token_url': 'https://api.twitter.com/2/oauth2/token',
        'userinfo_url': 'https://api.twitter.com/2/users/me?user.fields=profile_image_url,name,username',
        'scope': 'tweet.read users.read offline.access',
        'pkce': True,   # Twitter v2 mandates PKCE
        'extra_params': {},
        'env_client_id': 'TWITTER_CLIENT_ID',
        'env_client_secret': 'TWITTER_CLIENT_SECRET',
    },

    # ── Future Providers (add config when ready) ──────────────────────────
    'apple': {
        'name': 'Apple',
        'color': '#000000',
        'auth_url': 'https://appleid.apple.com/auth/authorize',
        'token_url': 'https://appleid.apple.com/auth/token',
        'userinfo_url': None,   # Apple returns info in the id_token
        'scope': 'name email',
        'pkce': False,
        'extra_params': {'response_mode': 'form_post'},
        'env_client_id': 'APPLE_CLIENT_ID',
        'env_client_secret': 'APPLE_CLIENT_SECRET',
    },

    'discord': {
        'name': 'Discord',
        'color': '#5865f2',
        'auth_url': 'https://discord.com/oauth2/authorize',
        'token_url': 'https://discord.com/api/oauth2/token',
        'userinfo_url': 'https://discord.com/api/users/@me',
        'scope': 'identify email',
        'pkce': False,
        'extra_params': {},
        'env_client_id': 'DISCORD_CLIENT_ID',
        'env_client_secret': 'DISCORD_CLIENT_SECRET',
    },

    'slack': {
        'name': 'Slack',
        'color': '#4a154b',
        'auth_url': 'https://slack.com/openid/connect/authorize',
        'token_url': 'https://slack.com/api/openid.connect.token',
        'userinfo_url': 'https://slack.com/api/openid.connect.userInfo',
        'scope': 'openid email profile',
        'pkce': False,
        'extra_params': {},
        'env_client_id': 'SLACK_CLIENT_ID',
        'env_client_secret': 'SLACK_CLIENT_SECRET',
    },

    'reddit': {
        'name': 'Reddit',
        'color': '#ff4500',
        'auth_url': 'https://www.reddit.com/api/v1/authorize',
        'token_url': 'https://www.reddit.com/api/v1/access_token',
        'userinfo_url': 'https://oauth.reddit.com/api/v1/me',
        'scope': 'identity',
        'pkce': False,
        'extra_params': {'duration': 'permanent'},
        'env_client_id': 'REDDIT_CLIENT_ID',
        'env_client_secret': 'REDDIT_CLIENT_SECRET',
    },

    'gitlab': {
        'name': 'GitLab',
        'color': '#fc6d26',
        'auth_url': 'https://gitlab.com/oauth/authorize',
        'token_url': 'https://gitlab.com/oauth/token',
        'userinfo_url': 'https://gitlab.com/oauth/userinfo',
        'scope': 'read_user openid email profile',
        'pkce': True,
        'extra_params': {},
        'env_client_id': 'GITLAB_CLIENT_ID',
        'env_client_secret': 'GITLAB_CLIENT_SECRET',
    },
}

# Providers shown on the login page (ordered)
ACTIVE_LOGIN_PROVIDERS = ['google', 'github']


def get_provider_config(provider_name: str) -> dict:
    """Return the provider config dict. Raises ValueError if unknown."""
    config = PROVIDERS.get(provider_name)
    if not config:
        raise ValueError(f"Unknown OAuth provider: '{provider_name}'")
    return config


def get_client_id(provider_name: str) -> str:
    """Read client_id from environment. Returns '' if not set."""
    cfg = get_provider_config(provider_name)
    return os.environ.get(cfg['env_client_id'], '')


def get_client_secret(provider_name: str) -> str:
    """Read client_secret from environment. Returns '' if not set."""
    cfg = get_provider_config(provider_name)
    env_key = cfg.get('env_client_secret')
    if not env_key:
        return ''
    return os.environ.get(env_key, '')


def is_provider_configured(provider_name: str) -> bool:
    """Return True only if both client_id and client_secret are set in environment."""
    return bool(get_client_id(provider_name) and get_client_secret(provider_name))
