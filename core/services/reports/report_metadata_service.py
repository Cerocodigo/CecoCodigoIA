# core/services/reports/report_metadata_service.py
# ==================================================
# Servicio de Metadata para generación IA de reportes
# ==================================================

from core.db.mongo.services.modules.module_query_service import (
    ModuleQueryService,
)
from core.db.mysql.services.mysql_metadata_service import (
    MySQLMetadataService,
)


class ReportMetadataService:
    """
    Servicio responsable de:

    - Proveer módulos disponibles en Mongo
    - Proveer metadata de tablas MySQL (estructura real)
    - Proveer palabras prohibidas SQL
    - Construir el contexto completo que se envía a la IA

    NO valida JSON.
    NO ejecuta SQL de negocio.
    NO persiste datos.
    """

    FORBIDDEN_KEYWORDS = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "REPLACE",
        "RENAME",
        "GRANT",
        "REVOKE",
        "CALL",
        "EXEC",
        "EXECUTE",
    ]

    # ==================================================
    # API pública
    # ==================================================

    @classmethod
    def build_generation_context(cls, *, company) -> dict:
        """
        Construye contexto completo para generación IA.
        """

        # =========================
        # 1️⃣ Módulos activos
        # =========================
        modules = ModuleQueryService.get_active_modules(company)
        available_modules = [m["_id"] for m in modules]

        # =========================
        # 2️⃣ Metadata MySQL real
        # =========================
        mysql_schema_metadata = MySQLMetadataService.get_schema_metadata(
            company=company
        )

        return {
            "estructura_reporte": cls._report_structure_contract(),
            "reglas_sql": cls._sql_rules_contract(),
            "modulos_disponibles": available_modules,
            "metadata_mysql": mysql_schema_metadata,
        }

    # ==================================================
    # Contrato estructural del Reporte
    # ==================================================

    @staticmethod
    def _report_structure_contract() -> dict:

        return {
            "estructura_general": {
                "nombre": "string",
                "descripcion": "string",
                "modulos": ["string"],
                "exportable": {
                    "pdf": "boolean",
                    "excel": "boolean",
                },
                "parametros": {
                    "variables": [],
                    "referencias": [],
                },
                "niveles": [
                    {
                        "nivel": "integer >= 0",
                        "query": "string SQL SELECT",
                        "columnas": [
                            {
                                "nombre": "string",
                                "alias": "string",
                                "visible": "boolean"
                            }
                        ],
                        "totales": [
                            {
                                "columna": "string",
                                "tipo": "SUM | COUNT | AVG"
                            }
                        ]
                    }
                ]
            },
            "reglas_jerarquia": {
                "nivel_0_obligatorio": True,
                "niveles_secuenciales": True,
                "vinculo_hijo_si_hay_siguiente": True,
                "vinculo_padre_si_hay_anterior": True,
                "solo_un_vinculo_por_nivel": True,
            },
        }

    # ==================================================
    # Reglas SQL
    # ==================================================

    @classmethod
    def _sql_rules_contract(cls) -> dict:

        return {
            "tipo_permitido": "SELECT únicamente",
            "joins_permitidos": True,
            "subqueries_permitidas": True,
            "group_by_permitido": True,
            "having_permitido": True,
            "limit_permitido": True,
            "offset_permitido": True,
            "forbidden_keywords": cls.FORBIDDEN_KEYWORDS,
            "reglas_vinculo": {
                "nombre_columna_hijo": "VINCULO_HIJO",
                "nombre_columna_padre": "VINCULO_PADRE",
                "no_mostrar_en_visualizacion": True,
            },
        }