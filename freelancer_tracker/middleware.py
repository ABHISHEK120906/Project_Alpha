"""
FreelanceTrack — Security & Rate Limiting Middleware
Enforces strict Content-Security-Policy (CSP), rate limiting, and security headers.
"""

import time
import ipaddress
import logging
from collections import defaultdict
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Trusted private/loopback networks (used for proxy IP validation) ──────────
_PRIVATE_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
]


class SecurityHeadersMiddleware:
    """
    Injects comprehensive security headers into every response.

    Headers set:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: restrictive
    - X-Permitted-Cross-Domain-Policies: none
    - Cross-Origin-Opener-Policy: same-origin
    - Cross-Origin-Resource-Policy: same-origin
    - Content-Security-Policy: strict with CDN allowlist
    - Strict-Transport-Security: production only
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._set_security_headers(response)
        return response

    def _set_security_headers(self, response):
        # Core headers — always present
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Disable Flash/PDF cross-domain requests
        response['X-Permitted-Cross-Domain-Policies'] = 'none'

        # Isolate browsing context — prevents Spectre-class attacks
        response['Cross-Origin-Opener-Policy'] = 'same-origin'

        # Prevent cross-origin resource embedding by default
        response['Cross-Origin-Resource-Policy'] = 'same-origin'

        # Restrict browser feature access
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), interest-cohort=()'
        )

        # Content Security Policy
        # Allows CDNs used in base.html: Bootstrap, FontAwesome, Chart.js, Google Fonts
        # 'unsafe-inline' on scripts is required for Django's template-inline JS;
        # a nonce-based CSP would require template-level changes — tracked separately.
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            (
                "style-src 'self' 'unsafe-inline' "
                "https://cdn.jsdelivr.net "
                "https://cdnjs.cloudflare.com "
                "https://fonts.googleapis.com"
            ),
            "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "upgrade-insecure-requests",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)

        # HSTS — only in production (set via settings too; belt-and-suspenders)
        if not getattr(settings, 'DEBUG', True):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'


class RateLimitMiddleware:
    """
    Sliding-window in-memory rate limiter for sensitive endpoints (/api/ and /login/).
    Protects against brute-force and Denial-of-Service (DoS) attacks.

    Limits (configurable via settings):
    - Auth endpoints (/login/, /register/): RATE_LIMIT_AUTH_PER_MIN (default: 5)
    - API endpoints (/api/): RATE_LIMIT_API_PER_MIN (default: 60)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.ip_timestamps: dict[str, list[float]] = defaultdict(list)

        # Configuration from settings
        self.API_LIMIT = getattr(settings, 'RATE_LIMIT_API_PER_MIN', 60)
        self.AUTH_LIMIT = getattr(settings, 'RATE_LIMIT_AUTH_PER_MIN', 5)
        self.WINDOW_SECONDS = 60

    def get_client_ip(self, request) -> str:
        """
        Extract the real client IP from request headers.
        Iterates X-Forwarded-For from right-to-left, skipping private/loopback
        addresses, to find the first public IP (the actual client).
        Falls back to REMOTE_ADDR.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ips = [ip.strip() for ip in x_forwarded_for.split(',') if ip.strip()]
            # Walk from rightmost (most trusted) to leftmost, pick first non-private
            for ip_str in reversed(ips):
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    if not ip_obj.is_private and not ip_obj.is_loopback:
                        return ip_str
                except ValueError:
                    continue
            # All hops were private (internal proxy chain) — use leftmost as client
            if ips:
                return ips[0]
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def __call__(self, request):
        path = request.path

        # Apply rate limiting only to API and Auth routes
        is_api = path.startswith('/api/')
        is_auth = path in ('/login/', '/register/')

        if is_api or is_auth:
            ip = self.get_client_ip(request)
            now = time.time()
            limit = self.AUTH_LIMIT if is_auth else self.API_LIMIT
            bucket_key = f"{ip}:{'auth' if is_auth else 'api'}"

            # Prune timestamps outside the sliding window
            timestamps = [t for t in self.ip_timestamps[bucket_key] if now - t < self.WINDOW_SECONDS]
            self.ip_timestamps[bucket_key] = timestamps

            if len(timestamps) >= limit:
                retry_after = int(self.WINDOW_SECONDS - (now - timestamps[0])) if timestamps else self.WINDOW_SECONDS
                logger.warning(
                    "Rate limit exceeded | ip=%s path=%s limit=%d window=%ds",
                    ip, path, limit, self.WINDOW_SECONDS,
                )
                response_data = {
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                    "status": 429,
                }
                res = JsonResponse(response_data, status=429)
                res['Retry-After'] = str(retry_after)
                return res

            self.ip_timestamps[bucket_key].append(now)

        return self.get_response(request)
