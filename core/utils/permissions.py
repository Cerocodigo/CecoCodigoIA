from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def require_permission(permission: str):
    """
    Decorador para proteger vistas por permiso.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            user_permissions = getattr(request, "permissions", set())

            if permission not in user_permissions:
                messages.error(
                    request,
                    "No tiene permisos para realizar esta acción."
                )
                return redirect("/")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
