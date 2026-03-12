from django.shortcuts import redirect


def logout_view(request):
    """
    Cierra sesión del usuario.
    """

    # Limpia toda la sesión
    request.session.flush()

    # Redirigir al login
    return redirect("accounts:login")
