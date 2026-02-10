# core/services/company_signature_service.py

import os
from datetime import datetime
from django.core.exceptions import ValidationError

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography import x509

from core.services.company_storage_service import CompanyStorageService


class CompanySignatureService:
    """
    Servicio encargado de la validación y guardado
    de la firma electrónica (.p12) de una empresa.
    """

    # =========================
    # Configuración general
    # =========================
    MAX_SIZE_MB = 5
    ALLOWED_EXTENSIONS = [".p12"]

    # =========================
    # Guardado de firma electrónica
    # =========================
    @staticmethod
    def save_signature(company_uid: str, signature_file) -> str | None:
        """
        Valida estructura básica y guarda el archivo .p12.
        Retorna la ruta relativa del archivo guardado.
        """

        # =========================
        # Archivo opcional
        # =========================
        if not signature_file:
            return None

        # =========================
        # Validar extensión
        # =========================
        _, ext = os.path.splitext(signature_file.name.lower())
        if ext not in CompanySignatureService.ALLOWED_EXTENSIONS:
            raise ValidationError("La firma electrónica debe ser un archivo .p12")

        # =========================
        # Validar tamaño
        # =========================
        size_mb = signature_file.size / (1024 * 1024)
        if size_mb > CompanySignatureService.MAX_SIZE_MB:
            raise ValidationError("El archivo .p12 no debe superar los 5MB")

        # =========================
        # Preparar rutas de almacenamiento
        # =========================
        base_path = CompanyStorageService.get_company_base_path(company_uid)
        firma_dir = os.path.join(base_path, "firma")

        filename = "firma.p12"
        full_path = os.path.join(firma_dir, filename)

        # =========================
        # Guardar archivo en disco
        # =========================
        try:
            with open(full_path, "wb+") as destination:
                for chunk in signature_file.chunks():
                    destination.write(chunk)
        except Exception:
            raise ValidationError("No se pudo guardar el archivo de firma electrónica")

        # Ruta relativa (consistente con logo y otros recursos)
        return f"companies/{company_uid}/firma/{filename}"

    # =========================
    # Validación criptográfica del .p12
    # =========================
    @staticmethod
    def validate_signature(
        p12_path: str,
        password: str | None = None
    ) -> dict:
        """
        Valida el contenido criptográfico de un archivo .p12.

        - Verifica que el archivo sea legible
        - Valida la contraseña (si existe)
        - Verifica vigencia del certificado

        Retorna un diccionario con información relevante del certificado.
        Lanza ValidationError si el archivo no es válido.
        """

        # =========================
        # Leer archivo .p12 desde disco
        # =========================
        try:
            with open(p12_path, "rb") as f:
                p12_data = f.read()
        except Exception:
            raise ValidationError("No se pudo leer el archivo .p12")

        # =========================
        # Cargar estructura PKCS12
        # =========================
        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                p12_data,
                password.encode() if password else None,
                backend=default_backend()
            )
        except Exception:
            raise ValidationError(
                "La contraseña es incorrecta o el archivo .p12 es inválido"
            )

        # =========================
        # Validar existencia de certificado
        # =========================
        if not certificate:
            raise ValidationError("El archivo .p12 no contiene un certificado válido")

        # =========================
        # Validar vigencia del certificado
        # =========================
        now = datetime.utcnow()

        if certificate.not_valid_before > now:
            raise ValidationError("El certificado digital aún no es válido")

        if certificate.not_valid_after < now:
            raise ValidationError("El certificado digital está vencido")

        # =========================
        # Extraer información relevante
        # =========================
        subject = certificate.subject

        def get_attr(oid):
            """
            Obtiene un atributo del subject del certificado
            de forma segura (puede no existir).
            """
            try:
                return subject.get_attributes_for_oid(oid)[0].value
            except Exception:
                return None

        cert_info = {
            "subject_cn": get_attr(x509.NameOID.COMMON_NAME),
            "issuer": certificate.issuer.rfc4514_string(),
            "serial_number": str(certificate.serial_number),
            "valid_from": certificate.not_valid_before,
            "valid_to": certificate.not_valid_after,
        }

        return cert_info
