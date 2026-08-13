"""
FreelanceTrack — Security & Rate Limiting Middleware
Enforces strict Content-Security-Policy (CSP), rate limiting, and security headers.
"""

import time
import ipaddress
from collections import defaultdict
from django.http import JsonResponse
from django.conf import settings


class SecurityHeadersMiddleware:
    """Injects security headers into every response."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security Headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        # Content Security Policy (CSP)
        # Note: Allows CDNs used in base.html (Bootstrap, FontAwesome, Chart.js, Google Fonts)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        response['Content-Security-Policy'] = csp


        # HSTS (Strict-Transport-Security) in production
        if not getattr(settings, 'DEBUG', True):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        return response


class RateLimitMiddleware:
    """
    Sliding window in-memory rate limiter for sensitive endpoints (/api/ and /login/).
    Protects against brute force and Denial of Service (DoS) attacks.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.ip_timestamps = defaultdict(list)
        
        # Configuration
        self.API_LIMIT = getattr(settings, 'RATE_LIMIT_API_PER_MIN', 100)
        self.AUTH_LIMIT = getattr(settings, 'RATE_LIMIT_AUTH_PER_MIN', 15)
        self.WINDOW_SECONDS = 60

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ips = [ip.strip() for ip in x_forwarded_for.split(',') if ip.strip()]
            for ip in reversed(ips):
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    if not ip_obj.is_private and not ip_obj.is_loopback:
                        return ip
                except ValueError:
                    continue
            if ips:
                return ips[0]
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def __call__(self, request):
        path = request.path

        # Apply rate limiting only to API and Auth routes
        is_api = path.startswith('/api/')
        is_auth = path in ['/login/', '/register/']

        if is_api or is_auth:
            ip = self.get_client_ip(request)
            now = time.time()
            limit = self.AUTH_LIMIT if is_auth else self.API_LIMIT
            bucket_key = f"{ip}:{path if is_auth else 'api'}"

            # Clean old timestamps outside the time window
            timestamps = [t for t in self.ip_timestamps[bucket_key] if now - t < self.WINDOW_SECONDS]
            self.ip_timestamps[bucket_key] = timestamps

            if len(timestamps) >= limit:
                retry_after = int(self.WINDOW_SECONDS - (now - timestamps[0])) if timestamps else self.WINDOW_SECONDS
                response_data = {
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                    "status": 429
                }
                res = JsonResponse(response_data, status=429)
                res['Retry-After'] = str(retry_after)
                return res

            self.ip_timestamps[bucket_key].append(now)

        return self.get_response(request)
