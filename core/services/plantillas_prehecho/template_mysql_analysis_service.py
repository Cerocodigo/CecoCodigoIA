# core/services/plantillas_prehecho/template_mysql_analysis_service.py

from core.db.sqlite.models.modelo_prehecho_jsons import (
    ModeloPrehechoJsons,
)

from core.services.plantillas_prehecho.template_mysql_table_query_service import (
    TemplateMySQLTableQueryService,
)

from core.services.plantillas_prehecho.template_mysql_conflict_builder_service import (
    TemplateMySQLConflictBuilderService,
)


# =========================
# Helper de normalización JSON
# =========================
def normalize_model(model):
    if not isinstance(model, dict):
        return model

    if "creado_en" in model and isinstance(model["creado_en"], dict):
        model["creado_en"] = model["creado_en"].get("$date")

    return model

class TemplateMySQLAnalysisService:
    """
    Servicio orquestador encargado
    de analizar conflictos MySQL
    antes de aplicar plantilla.
    """

    # =========================
    # Analizar aplicación
    # =========================
    @staticmethod
    def analyze_template_application(
        *,
        company,
        plantilla,
    ):
        """
        Analiza:

        - tablas actuales
        - registros existentes
        - conflictos con plantilla
        """

        # =========================
        # Obtener tablas actuales
        # =========================
        existing_tables = TemplateMySQLTableQueryService.get_tables_with_counts(
            company=company
        )
        
        # =========================
        # Obtener modelos plantilla
        # =========================
        template_models_json = ModeloPrehechoJsons.objects.filter(
            modelo=plantilla,
            activo=True,
            tipo="modelos",
        ).order_by("id")

        template_models = []
        for item in template_models_json:
            json_data = item.json

            if not json_data:
                continue

            # CASO 1: si ya es lista (tu caso real)
            if isinstance(json_data, list):
                template_models.extend([normalize_model(item) for item in json_data])
                continue

            # CASO 2: si fuera dict individual
            if isinstance(json_data, dict):
                template_models.append(normalize_model(json_data))
                continue

        # =========================
        # Construir conflictos
        # =========================
        try:
            tables = TemplateMySQLConflictBuilderService.build_conflict_summary(
                existing_tables=existing_tables,
                template_models=template_models,
            )
        except Exception as e:
            raise
        

        # =========================
        # Retorno final
        # =========================
        return {
            "requires_confirmation": (
                len(tables) > 0
            ),
            "tables": tables,
        }