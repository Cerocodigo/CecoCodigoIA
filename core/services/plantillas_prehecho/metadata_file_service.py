# core/services/plantillas_prehecho/metadata_file_service.py

import os
import uuid

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from core.services.plantillas_prehecho.metadata_storage_service import (MetadataStorageService)


class MetadataFileService:
    """
    Servicio encargado de validar y almacenar
    archivos dinámicos asociados a metadata
    de plantillas prehechas.
    """

    # =========================
    # Tipos soportados
    # =========================
    FILE_TYPES = {
        "imagen": {
            "extensions": [".png", ".jpg", ".jpeg"],
            "max_size_mb": 2,
            "directory": "imagenes",
        },

        "p12": {
            "extensions": [".p12"],
            "max_size_mb": 5,
            "directory": "firmas",
        },

        "archivo": {
            "extensions": [],
            "max_size_mb": 10,
            "directory": "archivos",
        },
    }

    # =========================
    # Validar tipo soportado
    # =========================
    @staticmethod
    def validate_supported_type(file_type: str) -> None:

        if file_type not in MetadataFileService.FILE_TYPES:
            raise ValidationError(
                f"Tipo de archivo no soportado: {file_type}"
            )

    # =========================
    # Validar extensión
    # =========================
    @staticmethod
    def validate_extension(
        filename: str,
        allowed_extensions: list,
    ) -> str:
        """
        Retorna extensión validada.
        """

        ext = os.path.splitext(filename)[1].lower()

        # =========================
        # Si no hay restricciones
        # =========================
        if not allowed_extensions:
            return ext

        if ext not in allowed_extensions:
            raise ValidationError(
                f"Extensión no permitida: {ext}"
            )

        return ext

    # =========================
    # Validar tamaño
    # =========================
    @staticmethod
    def validate_size(
        file_size: int,
        max_size_mb: int | float,
    ) -> None:

        size_mb = file_size / (1024 * 1024)

        if size_mb > max_size_mb:
            raise ValidationError(
                f"El archivo supera el límite de "
                f"{max_size_mb}MB"
            )

    # =========================
    # Generar nombre seguro
    # =========================
    @staticmethod
    def generate_safe_filename(
        extension: str,
    ) -> str:
        """
        Genera nombre único seguro.
        """

        random_id = uuid.uuid4().hex

        return f"{random_id}{extension}"

    # =========================
    # Guardar archivo metadata
    # =========================
    @staticmethod
    def save_file(
        *,
        company_id: str,
        uploaded_file: UploadedFile,
        file_type: str,
        custom_directory: str | None = None,
        allowed_extensions: list | None = None,
        max_size_mb: int | float | None = None,
    ) -> dict:
        """
        Guarda archivo metadata dinámico.

        Retorna:
        {
            "filename": "...",
            "relative_url": "...",
            "full_path": "...",
            "directory": "...",
        }
        """

        # =========================
        # Validar archivo
        # =========================
        if not uploaded_file:
            raise ValidationError(
                "No se recibió archivo"
            )

        # =========================
        # Validar tipo soportado
        # =========================
        MetadataFileService.validate_supported_type(
            file_type
        )

        type_config = (
            MetadataFileService.FILE_TYPES[file_type]
        )

        # =========================
        # Configuración final
        # =========================
        final_extensions = (
            allowed_extensions
            if allowed_extensions is not None
            else type_config["extensions"]
        )

        final_max_size_mb = (
            max_size_mb
            if max_size_mb is not None
            else type_config["max_size_mb"]
        )

        final_directory = (
            custom_directory
            if custom_directory
            else type_config["directory"]
        )

        # =========================
        # Validar extensión
        # =========================
        extension = (
            MetadataFileService.validate_extension(
                uploaded_file.name,
                final_extensions,
            )
        )

        # =========================
        # Validar tamaño
        # =========================
        MetadataFileService.validate_size(
            uploaded_file.size,
            final_max_size_mb,
        )

        # =========================
        # Validar directorio
        # =========================
        if (
            final_directory
            not in MetadataStorageService.ALLOWED_DIRECTORIES
        ):
            raise ValidationError(
                f"Directorio inválido: "
                f"{final_directory}"
            )
        # =========================
        # Garantizar estructura física
        # =========================
        MetadataStorageService.create_metadata_directories(
            company_id
        )

        # =========================
        # Obtener ruta física
        # =========================
        directory_path = (
            MetadataStorageService.get_metadata_directory_path(
                company_id=company_id,
                directory=final_directory,
            )
        )

        # =========================
        # Generar filename seguro
        # =========================
        safe_filename = (
            MetadataFileService.generate_safe_filename(
                extension
            )
        )

        full_path = os.path.join(
            directory_path,
            safe_filename,
        )

        # =========================
        # Guardar archivo
        # =========================
        try:

            with open(full_path, "wb+") as destination:

                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

        except Exception:
            raise ValidationError(
                "No se pudo guardar el archivo"
            )

        # =========================
        # URL relativa
        # =========================
        relative_url = (
            MetadataStorageService.build_relative_url(
                company_id=company_id,
                directory=final_directory,
                filename=safe_filename,
            )
        )

        # =========================
        # Retorno
        # =========================
        return {
            "filename": safe_filename,
            "relative_url": relative_url,
            "full_path": full_path,
            "directory": final_directory,
        }