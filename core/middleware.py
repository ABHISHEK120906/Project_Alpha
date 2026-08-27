from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse

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

        path = request.path.lower()

        # Admin Route Protection
        if any(path.startswith(prefix) for prefix in restricted_prefixes):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('core:login')}?next={request.path}")

            is_admin = (request.user.is_staff or request.user.is_superuser or
                        (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'))

            if not is_admin:
                messages.error(request, "403 Forbidden: You do not have permission to access the Super Admin Dashboard.")
                return redirect('core:forbidden')

        # Client Route Protection — require login (public register exempted; role check in views)
        if any(path.startswith(prefix) for prefix in client_prefixes):
            if not request.user.is_authenticated and not path.startswith('/client/register'):
                return redirect(f"{reverse('core:login')}?next={request.path}")

        # Maintenance Mode Interceptor
        try:
            from core.models import SystemSetting
            maintenance_mode = SystemSetting.get_setting('maintenance_mode', 'false').lower() in ['true', '1', 'yes']
            if maintenance_mode:
                is_admin = (request.user.is_authenticated and
                            (request.user.is_staff or request.user.is_superuser or
                             (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')))
                if not is_admin and not any(path.startswith(p) for p in ['/login', '/logout', '/static', '/media', '/forbidden']):
                    return render(request, 'maintenance.html', status=503)
        except Exception:
            pass

        response = self.get_response(request)
        return response
