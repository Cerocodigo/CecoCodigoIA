import os
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from core.services.company_storage_service import CompanyStorageService


class CompanyLogoService:
    """
    Maneja validación y guardado del logo de la empresa.
    """

    ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg"]
    MAX_SIZE_MB = 2

    @staticmethod
    def save_logo(company_uid: str, logo_file: UploadedFile) -> str | None:
        """
        Valida y guarda el logo de la empresa.
        Retorna la ruta relativa del logo guardado.
        """
        try:
            # =========================
            # Archivo opcional
            # =========================
            if not logo_file:
                return None

            # =========================
            # Validaciones
            # =========================
            ext = os.path.splitext(logo_file.name)[1].lower()
            if ext not in CompanyLogoService.ALLOWED_EXTENSIONS:
                raise ValidationError("Formato de logo inválido. Use PNG o JPG.")

            size_mb = logo_file.size / (1024 * 1024)
            if size_mb > CompanyLogoService.MAX_SIZE_MB:
                raise ValidationError("El logo no puede superar los 2MB.")


            # =========================
            # Guardar archivo
            # =========================
            base_path = CompanyStorageService.get_company_base_path(company_uid)
            logo_dir = os.path.join(base_path, "logo")

            filename = f"logo{ext}"
            full_path = os.path.join(logo_dir, filename)

            with open(full_path, "wb+") as destination:
                for chunk in logo_file.chunks():
                    destination.write(chunk)

            # =========================
            # Retornar ruta relativa
            # =========================
            url_path = CompanyLogoService.get_logo_url(company_uid, filename)
            return url_path
        except Exception as e:
            return ""


    @staticmethod
    def get_logo_url(company_uid: str, filename: str) -> str:
        """
        Retorna la ruta relativa del logo para su uso en la app.
        Ejemplo: /media/companies/<company_uid>/logo/logo.png
        """
        return f"/media/companies/{company_uid}/logo/{filename}"