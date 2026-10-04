from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *a, **kw):
            if request.user.role != role:
                raise PermissionDenied
            return view(request, *a, **kw)
        return wrapper
    return decorator


owner_required = role_required("owner")
tenant_required = role_required("tenant")
