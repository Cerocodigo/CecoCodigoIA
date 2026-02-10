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
    def validate_ruc_not_exists(ruc: str) -> None:
        """
        Valida que el RUC no exista ya en la base SQLite.
        """
        if Company.objects.filter(ruc=ruc).exists():
            raise ValidationError(
                "Ya existe una empresa registrada con este RUC"
            )
