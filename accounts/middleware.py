from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect

PROTECTED_PREFIXES = {"/owner/": "owner", "/tenant/": "tenant"}


class RoleAccessMiddleware:
    """Blocks anonymous users and wrong-role users from /owner/ and /tenant/ URLs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for prefix, role in PROTECTED_PREFIXES.items():
            if request.path.startswith(prefix):
                if not request.user.is_authenticated:
                    return redirect_to_login(request.get_full_path())
                if request.user.role != role:
                    messages.error(request, f"That area is only for {role}s.")
                    return redirect("rentals:property_list")
        return self.get_response(request)
