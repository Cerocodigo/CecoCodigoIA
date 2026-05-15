# core/services/plantillas_prehecho/template_metadata_replace_service.py

from core.db.mongo.services.plantillas_prehecho.metadata_query_service import (MetadataQueryService)

from core.db.mongo.services.plantillas_prehecho.template_import_query_service import (TemplateImportQueryService)


class TemplateMetadataReplaceService:
    """
    Servicio encargado de aplicar
    metadata MongoDB sobre documentos
    importados de plantilla.
    """

    # =========================
    # Ejecutar reemplazos
    # =========================
    @staticmethod
    def execute(
        *,
        company,
    ):
        """
        Ejecuta reemplazos metadata.
        """

        # =========================
        # Resetear flags aplicada
        # =========================
        reset_result = MetadataQueryService.reset_metadata_aplicada(
            company=company,
        )

        # =========================
        # Obtener metadata
        # =========================
        metadata_documents = MetadataQueryService.get_all_metadata(
            company=company,
        )

        processed = []
        skipped = []

        # =========================
        # Recorrer metadata
        # =========================
        for metadata in metadata_documents:
            metadata_id = metadata.get("_id")

            collection_name = metadata.get("coleccion_aplicar")
            condition = metadata.get("condicion_aplicar") or {}

            field_name = metadata.get("campo_aplicar")
            element = metadata.get("elemento_aplicar")

            replace_value = metadata.get("valor")

            # =========================
            # Normalizar strings
            # =========================
            if isinstance(field_name, str):
                field_name = field_name.strip()

            if isinstance(element, str):
                element = element.strip()

            # =========================
            # Validar colección
            # =========================
            if not collection_name:
                skipped.append(
                    {
                        "metadata_id": metadata_id,
                        "reason": "missing_collection",
                    }
                )
                continue

            # =========================
            # Validar exclusividad
            # =========================
            # NO pueden estar ambos vacíos
            # =========================
            field_empty = (
                field_name in [None, "", "*"]
            )

            element_empty = (
                element in [None,""]
            )

            if (field_empty and element_empty):
                skipped.append(
                    {
                        "metadata_id": metadata_id,
                        "reason": "field_and_element_empty",
                    }
                )
                continue

            # =========================
            # Obtener documentos
            # =========================
            documents = TemplateImportQueryService.get_documents(
                company=company,
                collection_name=collection_name,
                filters=condition,
            )
            
            if not documents:
                skipped.append(
                    {
                        "metadata_id": metadata_id,
                        "reason": "no_documents_found",
                    }
                )
                continue

            applied_count = 0

            # =========================
            # Recorrer documentos
            # =========================
            for document in documents:
                updated_fields = {}

                # =========================
                # Caso:
                # Aplicar sobre todo el documento
                # =========================
                if field_name in ["","*",None]:
                    for key, current_value in document.items():
                        # =========================
                        # Ignorar _id
                        # =========================
                        if key == "_id":
                            continue

                        updated_value = TemplateMetadataReplaceService.build_updated_value(
                            current_value=current_value,
                            element=element,
                            replace_value=replace_value,
                        )

                        if updated_value != current_value:
                            updated_fields[key] = (updated_value)

                # =========================
                # Caso:
                # Campo específico
                # =========================
                else:
                    current_value = document.get(field_name)

                    # =========================
                    # Campo inexistente
                    # =========================
                    if current_value is None:
                        continue

                    # =========================
                    # Construir valor final
                    # =========================
                    updated_value = TemplateMetadataReplaceService.build_updated_value(
                        current_value=current_value,
                        element=element,
                        replace_value=replace_value,
                    )

                    # =========================
                    # Detectar cambios
                    # =========================
                    if updated_value != current_value:
                        updated_fields[field_name] = updated_value

                # =========================
                # Sin cambios
                # =========================
                if not updated_fields:
                    continue

                # =========================
                # Actualizar documento
                # =========================
                TemplateImportQueryService.update_document(
                    company=company,
                    collection_name=collection_name,
                    document_id=document["_id"],
                    update_data=updated_fields,
                )

                applied_count += 1

            # =========================
            # Actualizar metadata
            # =========================
            if applied_count > 0:
                MetadataQueryService.upsert_metadata(
                    company=company,
                    document={
                        **metadata,
                        "aplicada": "Si",
                    },
                )

            processed.append(
                {
                    "metadata_id": metadata_id,
                    "collection": collection_name,
                    "applied_count": applied_count,
                }
            )

        # =========================
        # Resultado final
        # =========================
        return {
            "success": True,
            "reset_result": reset_result,
            "processed": processed,
            "skipped": skipped,
        }

    # =========================
    # Construir valor actualizado
    # =========================
    @staticmethod
    def build_updated_value(
        *,
        current_value,
        element,
        replace_value,
    ):
        """
        Construye valor final
        según reglas metadata.
        """

        # =========================
        # Caso:
        # Reemplazo parcial string
        # =========================
        if (isinstance(current_value, str) and element not in [None,"",] and element in current_value):
            return current_value.replace(
                element,
                str(replace_value),
            )

        # =========================
        # Caso:
        # Igualdad exacta
        # =========================
        if current_value == element:

            return replace_value

        # =========================
        # Caso:
        # Reemplazo total campo
        # elemento=""
        # =========================
        if element in [None,"",]:

            return replace_value

        # =========================
        # Sin cambios
        # =========================
        return current_value