from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class UserRestrictionMiddleware:
    """
    FEATURE 16 — User Restrictions:
    Enforces that non-admin/non-staff users cannot access /admin/ or admin management APIs.
    Redirects unauthorized attempts to 403 Forbidden page or User Dashboard.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        restricted_prefixes = ['/admin', '/superadmin', '/api/v1/admin']
        
        path = request.path.lower()
        if any(path.startswith(prefix) for prefix in restricted_prefixes):
            if request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, "403 Forbidden: You do not have permission to access administration settings.")
                return redirect('core:forbidden')
        
        response = self.get_response(request)
        return response
