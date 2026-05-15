# core/services/plantillas_prehecho/template_mysql_conflict_builder_service.py


class TemplateMySQLConflictBuilderService:
    """
    Servicio encargado de construir
    resumen de conflictos entre:

    - tablas actuales MySQL
    - tablas definidas en plantilla
    """

    # =========================
    # Construir resumen
    # =========================
    @staticmethod
    def build_conflict_summary(
        *,
        existing_tables: list,
        template_models: list,
    ):
        """
        Construye payload estructurado
        para frontend.
        """
        template_table_names = set()

        # =========================
        # Extraer tablas plantilla
        # =========================
        for model in template_models:
            table_name = model.get("tabla")

            if not table_name:
                continue

            template_table_names.add(
                table_name
            )


        results = []
        # =========================
        # Comparar tablas actuales
        # =========================
        for table_data in existing_tables:
            table_name = (table_data["table_name"])
            record_count = (table_data["record_count"])

            exists_in_template = (
                table_name in template_table_names
            )

            results.append(
                {
                    "table_name": table_name,
                    "current_records": (
                        record_count
                    ),
                    "exists_in_template": (
                        exists_in_template
                    ),
                    "default_action": (
                        "keep"
                        if exists_in_template
                        else "delete"
                    ),
                }
            )
        
        return results