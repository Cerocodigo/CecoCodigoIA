# core/services/plantillas_prehecho/metadata_apply_service.py

from core.db.mongo.services.plantillas_prehecho.metadata_query_service import (
    MetadataQueryService,
)

from core.services.plantillas_prehecho.metadata_file_service import (
    MetadataFileService,
)


class MetadataApplyService:
    """
    Servicio encargado de procesar
    metadata dinámica y aplicarla
    en MongoDB.
    """

    # =========================
    # Aplicar metadata
    # =========================
    @staticmethod
    def apply_metadata(
        *,
        company,
        metadata_definition,
        request_files,
        request_post,
    ):
        """
        Procesa metadata dinámica enviada
        desde frontend.

        Reglas:
        - _id = variable
        - si existe -> reemplaza
        - si no existe -> inserta
        """

        processed_documents = []

        # =========================
        # Recorrer definición
        # =========================
        for item in metadata_definition:
            variable = item["variable"]
            input_type = item["tipo"]
            metadata_config = item["metadata"]
            metadata_type = metadata_config["tipo"]
            valor_final = None

            # =========================
            # Archivos
            # =========================
            if input_type in ["imagen", "p12"]:
                uploaded_file = request_files.get(
                    variable
                )

                if uploaded_file:
                    saved_file = (
                        MetadataFileService.save_file(
                            company_id=str(company.id),
                            uploaded_file=uploaded_file,
                            file_type=input_type,
                        )
                    )
                    valor_final = (
                        saved_file["relative_url"]
                    )

            # =========================
            # Valores normales
            # =========================
            else:
                valor_final = request_post.get(
                    variable,
                    "",
                )
            # =========================
            # Documento metadata
            # =========================
            document = {
                "_id": variable,
                "variable": variable,
                "valor": valor_final,
                "tipo": metadata_type,
                "aplicada": "No",
                "coleccion_aplicar": (
                    metadata_config[
                        "coleccion_aplicar"
                    ]
                ),
                "condicion_aplicar": (
                    metadata_config[
                        "condicion_aplicar"
                    ]
                ),
                "campo_aplicar": (
                    metadata_config[
                        "campo_aplicar"
                    ]
                ),
                "elemento_aplicar": (
                    metadata_config[
                        "elemento_aplicar"
                    ]
                ),
            }

            MetadataQueryService.upsert_metadata(
                company=company,
                document=document,
            )

            processed_documents.append(
                document
            )

        return processed_documents