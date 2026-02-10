import httpx
from django.core.exceptions import ValidationError


class SriRucService:
    """
    Servicio de validación de RUC contra el SRI.
    Aislado de vistas y modelos.
    """

    BASE_URL = (
        "https://srienlinea.sri.gob.ec/"
        "sri-catastro-sujeto-servicio-internet/"
        "rest/Persona/obtenerPersonaDesdeRucPorIdentificacion"
    )

    @staticmethod
    def validate_ruc(ruc: str) -> dict:
        """
        Valida un RUC consultando el SRI.
        Retorna el payload si es válido.
        Lanza ValidationError si no lo es.
        """

        url = f"{SriRucService.BASE_URL}?numeroRuc={ruc}"

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
        except httpx.RequestError:
            raise ValidationError(
                "No fue posible conectar con el servicio del SRI. Intenta más tarde."
            )

        if response.status_code != 200:
            raise ValidationError(
                "Error al validar el RUC en el SRI"
            )

        try:
            data = response.json()
        except ValueError:
            raise ValidationError(
                "Respuesta inválida del SRI al validar el RUC"
            )

        # El SRI devuelve None o estructura vacía si no existe
        if not data:
            raise ValidationError(
                "El RUC ingresado no existe según el SRI"
            )

        # Validaciones mínimas esperadas
        if not data.get("identificacion"):
            raise ValidationError(
                "El RUC no es válido según el SRI"
            )

        return data
