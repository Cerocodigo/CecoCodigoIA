from django.core.exceptions import ValidationError

from core.db.sqlite.models.company import Company


class CompanyValidationService:
    """
    Servicio de validaciones previas a la creación de una empresa.
    NO crea datos.
    NO accede a request / response.
    Lanza ValidationError si algo no cumple reglas.
    """
        
    @staticmethod
    def validate_nombre_comercial_not_exists(nombre_comercial: str) -> None:
        """
        Valida que el nombre comercial no exista ya en la base SQLite.
        """
        if Company.objects.filter(nombre_comercial__iexact=nombre_comercial).exists():
            raise ValidationError(
                "Ya existe una empresa registrada con este nombre comercial"
            )
