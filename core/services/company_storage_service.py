# core/services/company_storage_service.py

import os
import shutil
from django.conf import settings


class CompanyStorageService:
    """
    Servicio encargado de manejar la estructura
    de carpetas físicas por empresa.
    """

    @staticmethod
    def get_company_base_path(company_uid: str) -> str:
        """
        Retorna la ruta base física de una empresa.

        Ejemplo:
        MEDIA_ROOT/companies/<company_uid>/
        """
        try:
            return os.path.join(
                settings.MEDIA_ROOT,
                "companies",
                company_uid
            )
        except Exception as e:
            raise e

    @staticmethod
    def create_company_directories(company_uid: str) -> dict:
        """
        Crea la estructura completa de carpetas
        asociadas a una empresa.

        Retorna un diccionario con las rutas creadas.
        """

        base_path = CompanyStorageService.get_company_base_path(company_uid)

        paths = {
            "base": base_path,
            "logo": os.path.join(base_path, "logo"),
            "firma": os.path.join(base_path, "firma"),
            "docs": os.path.join(base_path, "docs"),
        }

        # Crear todas las carpetas necesarias
        for path in paths.values():
            os.makedirs(path, exist_ok=True)

        return paths

    @staticmethod
    def delete_company_directories(company_uid: str) -> None:
        """
        Elimina completamente la carpeta de una empresa.

        ⚠️ Uso previsto:
        - rollback cuando falla creación de empresa
        - errores al guardar logo o firma
        """

        base_path = CompanyStorageService.get_company_base_path(company_uid)

        # Seguridad básica: evitar borrar fuera de MEDIA_ROOT
        media_root = os.path.abspath(settings.MEDIA_ROOT)
        base_path = os.path.abspath(base_path)

        if not base_path.startswith(media_root):
            raise RuntimeError(
                "Intento de eliminar un directorio fuera de MEDIA_ROOT"
            )

        if os.path.exists(base_path):
            shutil.rmtree(base_path)
