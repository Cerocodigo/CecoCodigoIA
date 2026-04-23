# core/db/mysql/services/provision_company_database.py
# ====================================================
# Servicio de provisioning MySQL por empresa
# ====================================================

import secrets
import string

from core.db.mysql.connection import MySQLConnectionFactory
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.exceptions import (
    MySQLServiceError,
    MySQLConfigurationError,
    MySQLConnectionError,
    MySQLExecutionError,
)


class MySQLProvisionService:
    """
    Servicio responsable de:
    - Crear base de datos MySQL por empresa
    - Crear usuario MySQL dedicado
    - Asignar privilegios completos sobre su base

    Este servicio:
    - NO conoce Django ORM
    - NO guarda modelos
    - NO depende de Company
    - Devuelve SOLO credenciales
    """

    # =========================
    # Utilidades internas
    # =========================

    @staticmethod
    def _generate_password(length: int = 16) -> str:
        if length < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")

        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*-_=+"
        # Garantizar al menos uno de cada tipo
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special),
        ]

        # Completar con mezcla total
        all_chars = lowercase + uppercase + digits + special
        password += [secrets.choice(all_chars) for _ in range(length - 4)]

        # Mezclar para evitar patrones
        secrets.SystemRandom().shuffle(password)

        return "".join(password)

    # =========================
    # API pública
    # =========================

    @staticmethod
    def provision_company_database(*, mysql_server, db_name: str) -> dict:
        """
        Provisiona infraestructura MySQL para una empresa.

        Crea:
        - Base de datos
        - Usuario MySQL
        - Permisos completos sobre la base

        Retorna:
        {
            "db_user": str,
            "db_password": str
        }
        """

        # =========================
        # Validaciones mínimas
        # =========================
        if not mysql_server:
            raise MySQLConfigurationError(
                "Servidor MySQL no proporcionado"
            )

        if not db_name:
            raise MySQLConfigurationError(
                "Nombre de base de datos MySQL no proporcionado"
            )
        if not all([
            mysql_server.host,
            mysql_server.port,
            mysql_server.username,
            # mysql_server.password, # producción.
        ]):
            raise MySQLConfigurationError(
                "El servidor MySQL no tiene credenciales administrativas completas"
            )

        # =========================
        # Generar credenciales
        # =========================
        db_user = f"user_{db_name}"
        db_password = MySQLProvisionService._generate_password()

        # =========================
        # Conexión administrativa
        # =========================
        try:
            root_connection = MySQLConnectionFactory.get_root_connection(
                host=mysql_server.host,
                port=mysql_server.port,
                username=mysql_server.username,
                password=mysql_server.password,
            )
        except Exception as e:
            raise MySQLConnectionError(
                "No se pudo establecer conexión administrativa con MySQL",
                original_exception=e,
            )

        executor = MySQLExecutor(root_connection)

        # =========================
        # Provisioning
        # =========================
        try:
            # 1️⃣ Crear base de datos
            executor.execute(
                f"""
                CREATE DATABASE IF NOT EXISTS `{db_name}`
                CHARACTER SET utf8mb4
                COLLATE utf8mb4_unicode_ci
                """
            )

            # 2️⃣ Crear usuario
            executor.execute(
                f"CREATE USER IF NOT EXISTS '{db_user}'@'%%' IDENTIFIED BY %s",
                (db_password,),
            )


            # 3️⃣ Asignar permisos
            executor.execute(
                f"""
                GRANT ALL PRIVILEGES ON `{db_name}`.*
                TO '{db_user}'@'%%'
                """
            )

            executor.execute("FLUSH PRIVILEGES")

        except MySQLServiceError:
            raise

        except Exception as e:
            raise MySQLExecutionError(
                "Error durante el provisioning MySQL de la empresa",
                original_exception=e,
            )

        finally:
            try:
                root_connection.close()
            except Exception:
                pass

        # =========================
        # Retorno limpio
        # =========================
        return {
            "db_user": db_user,
            "db_password": db_password,
        }
