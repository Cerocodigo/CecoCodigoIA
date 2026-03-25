# services/ui/message_service.py
# =====================================================
# Servicio para manejar mensajes temporales en la interfaz (éxito, error, etc.)
# =====================================================
def set_view_msg(request, type_, text):
    """
    Guarda un mensaje temporal en la sesión para mostrarlo en la siguiente vista.
    type_: "success", "danger", "warning", etc.
    text: El mensaje a mostrar
    """
    request.session["view_msg"] = {
        "type": type_,
        "text": text
    }

def pop_view_msg(request):
    """
    Obtiene y elimina el mensaje temporal de la sesión.
    Retorna:
        dict con keys "type" y "text", o None si no hay mensaje
    """
    return request.session.pop("view_msg", None)