# core/services/reports/report_ai_service.py
# ==================================================
# Servicio de generación IA de Reportes
# ==================================================

import json

from core.services.ai.openai_client import OpenAIClient

from core.services.reports.report_metadata_service import (
    ReportMetadataService,
)
from core.services.reports.report_json_validator import (
    ReportJSONValidator,
)


class ReportAIService:
    """
    Orquestador de generación de reportes mediante IA.

    Flujo:
    1. Construye contexto estructural
    2. Genera prompt
    3. Invoca IA (OpenAI)
    4. Valida JSON generado
    5. Reintenta hasta 3 veces si hay errores
    6. Devuelve resultado final

    NO persiste.
    NO ejecuta SQL.
    """

    MAX_RETRIES = 3

    # ==================================================
    # API pública
    # ==================================================

    @classmethod
    def generate_report_definition(
        cls,
        *,
        company,
        user_prompt: str,
    ) -> dict:
        """
        Genera definición completa de reporte vía IA.

        Devuelve:
        {
            "success": bool,
            "report_definition": dict | None,
            "errors": list[str]
        }
        """

        # =========================
        # 1️⃣ Construir contexto
        # =========================
        context = ReportMetadataService.build_generation_context(
            company=company
        )

        # =========================
        # 2️⃣ Inicializar cliente OpenAI
        # =========================
        openai_client = OpenAIClient.get_client()
        accumulated_errors: list[str] = []

        # =========================
        # 3️⃣ Intentos controlados
        # =========================
        for attempt in range(cls.MAX_RETRIES + 1):

            prompt = cls._build_prompt(
                user_prompt=user_prompt,
                context=context,
                previous_errors=accumulated_errors if attempt > 0 else [],
            )

            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0,
                    messages=[
                        {
                            "role": "system",
                            "content": "Responde únicamente con JSON válido.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                )
                ai_response = (
                    response.choices[0]
                    .message.content
                    .strip()
                )
            except Exception as e:
                accumulated_errors.append(
                    f"Error al invocar la IA: {str(e)}"
                )
                continue

            # =========================
            # 4️⃣ Validar JSON
            # =========================
            try:
                report_definition = json.loads(ai_response)
            except json.JSONDecodeError:
                accumulated_errors.append(
                    "La IA no devolvió un JSON válido."
                )
                continue

            validation = ReportJSONValidator.validate(
                report_definition
            )

            if validation["is_valid"]:
                return {
                    "success": True,
                    "report_definition": report_definition,
                    "errors": [],
                }

            accumulated_errors = validation["errors"]

        # =========================
        # 5️⃣ Fallo definitivo
        # =========================
        accumulated_errors.append(
            "No fue posible generar un reporte válido. "
            "Por favor, proporciona más detalles sobre el tipo de reporte que deseas."
        )

        return {
            "success": False,
            "report_definition": None,
            "errors": accumulated_errors,
        }

    # ==================================================
    # Construcción de Prompt
    # ==================================================

    @staticmethod
    def _build_prompt(
        *,
        user_prompt: str,
        context: dict,
        previous_errors: list[str],
    ) -> str:
        """
        Construye el prompt estructurado que se envía a la IA.
        """

        prompt_parts = []

        prompt_parts.append(
            "Genera un JSON válido para definir un reporte dinámico."
        )

        prompt_parts.append(
            "Debes respetar estrictamente la estructura y reglas indicadas."
        )

        prompt_parts.append("\n=== ESTRUCTURA REQUERIDA ===")
        prompt_parts.append(
            json.dumps(
                context["estructura_reporte"],
                indent=2,
                ensure_ascii=False,
            )
        )

        prompt_parts.append("\n=== REGLAS SQL ===")
        prompt_parts.append(
            json.dumps(
                context["reglas_sql"],
                indent=2,
                ensure_ascii=False,
            )
        )

        prompt_parts.append("\n=== MÓDULOS DISPONIBLES ===")
        prompt_parts.append(
            json.dumps(
                context["modulos_disponibles"],
                indent=2,
                ensure_ascii=False,
            )
        )

        prompt_parts.append("\n=== METADATA MYSQL ===")
        prompt_parts.append(
            json.dumps(
                context["metadata_mysql"],
                indent=2,
                ensure_ascii=False,
            )
        )

        if previous_errors:
            prompt_parts.append(
                "\n=== ERRORES DETECTADOS EN INTENTO ANTERIOR ==="
            )
            for err in previous_errors:
                prompt_parts.append(f"- {err}")

            prompt_parts.append(
                "\nCorrige TODOS los errores listados."
            )

        prompt_parts.append("\n=== SOLICITUD DEL USUARIO ===")
        prompt_parts.append(user_prompt)

        prompt_parts.append(
            "\nDevuelve únicamente el JSON, sin texto adicional."
        )

        return "\n".join(prompt_parts)