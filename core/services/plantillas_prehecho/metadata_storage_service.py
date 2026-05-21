# core/services/plantillas_prehecho/metadata_storage_service.py

import os
from django.conf import settings


class MetadataStorageService:
    """
    Maneja almacenamiento físico asociado
    a metadata dinámica de plantillas prehechas.
    """

    # =========================
    # Directorios permitidos
    # =========================
    ALLOWED_DIRECTORIES = [
        "imagenes",
        "firmas",
        "archivos",
        "temp",
    ]

    # =========================
    # Base metadata path
    # =========================
    @staticmethod
    def get_metadata_base_path(company_id: str) -> str:
        """
        Retorna ruta base metadata.

        Ejemplo:
        MEDIA_ROOT/companies/<company_id>/metadata/
        """

        return os.path.join(
            settings.MEDIA_ROOT,
            "companies",
            company_id,
            "metadata",
        )

    # =========================
    # Obtener subdirectorio
    # =========================
    @staticmethod
    def get_metadata_directory_path(
        company_id: str,
        directory: str,
    ) -> str:
        """
        Retorna ruta física de subdirectorio metadata.
        """

        if directory not in MetadataStorageService.ALLOWED_DIRECTORIES:
            raise ValueError(
                f"Directorio metadata inválido: {directory}"
            )

        return os.path.join(
            MetadataStorageService.get_metadata_base_path(company_id),
            directory,
        )

    # =========================
    # Crear estructura metadata
    # =========================
    @staticmethod
    def create_metadata_directories(
        company_id: str,
    ) -> dict:
        """
        Crea estructura completa metadata.
        """

        base_path = (
            MetadataStorageService.get_metadata_base_path(
                company_id
            )
        )

        paths = {
            "base": base_path,
        }

        # =========================
        # Crear directorios permitidos
        # =========================
        for directory in MetadataStorageService.ALLOWED_DIRECTORIES:
            dir_path = os.path.join(
                base_path,
                directory,
            )
            os.makedirs(
                dir_path,
                exist_ok=True,
            )
            paths[directory] = dir_path
        return paths

    # =========================
    # Obtener URL relativa
    # =========================
    @staticmethod
    def build_relative_url(
        company_id: str,
        directory: str,
        filename: str,
    ) -> str:
        """
        Construye URL relativa utilizable
        dentro de MongoDB o frontend.

        Ejemplo:
        /media/companies/15/metadata/imagenes/logo.png
        """

        if directory not in MetadataStorageService.ALLOWED_DIRECTORIES:
            raise ValueError(
                f"Directorio metadata inválido: {directory}"
            )

        return (
            f"/media/companies/"
            f"{company_id}/metadata/"
            f"{directory}/{filename}"
        )