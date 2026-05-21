# core/services/plantillas_prehecho/apply_prebuilt_template_service.py

from core.db.sqlite.models.modelo_prehecho_jsons import (ModeloPrehechoJsons)

from core.services.plantillas_prehecho.metadata_validation_service import (MetadataValidationService)
from core.services.plantillas_prehecho.metadata_apply_service import (MetadataApplyService)

from core.db.mongo.services.plantillas_prehecho.template_cleanup_service import (TemplateCleanupService)
from core.db.mongo.services.plantillas_prehecho.template_import_query_service import (TemplateImportQueryService)

from core.services.plantillas_prehecho.template_mysql_strategy_service import (TemplateMySQLStrategyService)
from core.services.plantillas_prehecho.template_mysql_seed_service import (TemplateMySQLSeedService)
from core.services.plantillas_prehecho.template_metadata_replace_service import (TemplateMetadataReplaceService)

class ApplyPrebuiltTemplateService:
    """
    Pipeline principal
    de aplicación de plantilla prehecha.
    """

    # =========================
    # Apply
    # =========================
    @staticmethod
    def apply(*, company, plantilla, request_files, request_post, strategy):
        # =========================
        # Consolidar metadata definition
        # =========================
        metadata_definition = []

        ejecuciones = plantilla.ejecuciones.filter(
            activo=True
        ).order_by("id")

        for ejecucion in ejecuciones:
            data_variables_mongo = ejecucion.data_variables_mongo or []

            if not data_variables_mongo:
                continue

            # =========================
            # Validar estructura
            # =========================
            MetadataValidationService.validate_structure(
                data_variables_mongo=data_variables_mongo,
            )

            metadata_definition.extend(data_variables_mongo)

        # =========================
        # Aplicar metadata
        # =========================
        processed_documents = MetadataApplyService.apply_metadata(
            company=company,
            metadata_definition=metadata_definition,
            request_files=request_files,
            request_post=request_post,
        )


        # =========================
        # Limpiar colecciones MongoDB 
        # =========================
        cleanup_result = TemplateCleanupService.cleanup_company_database(
            company=company,
        )

        # =========================
        # Obtener JSONs activos
        # =========================
        template_jsons = (
            ModeloPrehechoJsons.objects.filter(
                modelo=plantilla,
                activo=True,
            ).order_by("id")
        )

        # =========================
        # Importar colecciones
        # =========================
        imported_collections = []
        for template_json in template_jsons:
            collection_name = template_json.tipo
            documents = template_json.json or []

            if not isinstance(documents,list,):
                continue

            inserted_ids = TemplateImportQueryService.insert_many_documents(
                company=company,
                collection_name=collection_name,
                documents=documents,
            )
            
            imported_collections.append(
                {
                    "collection": collection_name,
                    "inserted_count": len(
                        inserted_ids
                    ),
                }
            )

        # =========================
        # Ejecutar estrategia MySQL ((keep) Mantener registros o (clean) Instalación limpia)
        # =========================
        mysql_strategy_result = TemplateMySQLStrategyService.execute_strategy(
            company=company,
            plantilla=plantilla,
            strategy=strategy,
        )


        # =========================
        # Ejecutar inserts MySQL
        # =========================
        mysql_seed_result = TemplateMySQLSeedService.execute_seed(
            company=company,
            ejecuciones=ejecuciones,
        )
        

        # =========================
        # Metadata replacements
        # =========================
        metadata_replace_result = TemplateMetadataReplaceService.execute(
            company=company,
        )


        # =========================
        # Resultado final
        # =========================
        return {
            "processed_metadata_count": len(
                processed_documents
            ),
            "imported_collections": (
                imported_collections
            ),
            "cleanup_result": (
                cleanup_result
            ),
            "mysql_strategy_result": (
                mysql_strategy_result
            ),
            "mysql_seed_result": (
                mysql_seed_result
            ),
            "metadata_replace_result": (
                metadata_replace_result
            ),
        }