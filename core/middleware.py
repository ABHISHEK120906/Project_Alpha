import logging

from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse

security_logger = logging.getLogger('security')


def _get_client_ip(request) -> str:
    """Extract the best-guess client IP for logging purposes."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


class UserRestrictionMiddleware:
    """
    Enforces that non-admin/non-staff users cannot access /admin-dashboard/ or admin management APIs.
    If a user manually enters an Admin URL: Returns 403 Forbidden or redirects to User Dashboard.
    Also handles Maintenance Mode enforcement.
    Client routes (/client/) and Freelancer routes (/freelancer/) require authentication (public register routes exempted);
    role checks are performed inside respective views and API decorators.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        restricted_prefixes = ['/admin-dashboard', '/admin/', '/superadmin', '/api/v1/admin']
        client_prefixes = ['/client/']
        freelancer_prefixes = ['/freelancer/']

        path = request.path.lower()
        ip = _get_client_ip(request)

        # ── Admin Route Protection ─────────────────────────────────────────────
        if any(path.startswith(prefix) for prefix in restricted_prefixes):
            if not request.user.is_authenticated:
                security_logger.info(
                    "Unauthenticated admin access attempt | ip=%s path=%s",
                    ip, request.path,
                )
                return redirect(f"{reverse('core:login')}?next={request.path}")

            is_admin = (
                request.user.is_staff
                or request.user.is_superuser
                or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')
            )

            if not is_admin:
                security_logger.warning(
                    "403 Forbidden admin route | user=%s ip=%s path=%s",
                    request.user.username, ip, request.path,
                )
                if '/api/' in path:
                    return JsonResponse({'error': '403 Forbidden: Administrator access required.'}, status=403)
                messages.error(request, "403 Forbidden: You do not have permission to access the Super Admin Dashboard.")
                return redirect('core:forbidden')

        # ── Client Route Protection ────────────────────────────────────────────
        # Require login; public register route exempted; role checks inside views.
        if any(path.startswith(prefix) for prefix in client_prefixes):
            if not request.user.is_authenticated and not path.startswith('/client/register'):
                security_logger.info(
                    "Unauthenticated client route access | ip=%s path=%s",
                    ip, request.path,
                )
                if '/api/' in path:
                    return JsonResponse({'error': 'Authentication required.'}, status=401)
                return redirect(f"{reverse('core:login')}?next={request.path}")

        # ── Freelancer Route Protection ────────────────────────────────────────
        # Require login; public register route exempted; role checks inside views.
        if any(path.startswith(prefix) for prefix in freelancer_prefixes):
            if not request.user.is_authenticated and not path.startswith('/freelancer/register'):
                security_logger.info(
                    "Unauthenticated freelancer route access | ip=%s path=%s",
                    ip, request.path,
                )
                if '/api/' in path:
                    return JsonResponse({'error': 'Authentication required.'}, status=401)
                return redirect(f"{reverse('core:login')}?next={request.path}")

        # ── Maintenance Mode Interceptor ───────────────────────────────────────
        try:
            from core.models import SystemSetting
            maintenance_mode = SystemSetting.get_setting('maintenance_mode', 'false').lower() in ['true', '1', 'yes']
            if maintenance_mode:
                is_admin = (
                    request.user.is_authenticated
                    and (
                        request.user.is_staff
                        or request.user.is_superuser
                        or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')
                    )
                )
                bypass_paths = ('/login', '/logout', '/static', '/media', '/forbidden')
                if not is_admin and not any(path.startswith(p) for p in bypass_paths):
                    return render(request, 'maintenance.html', status=503)
        except Exception:
            pass

        response = self.get_response(request)
        return response

