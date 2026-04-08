# core/services/modules/model_sync_orchestrator_service.py
# ==================================================
# Orquestador principal de validación y corrección de modelos
# ==================================================

from core.services.modules.model_correction_service import ModelCorrectionService
from core.services.modules.model_validator_service import ModelValidatorService


class ModelSyncOrchestratorService:
    """
    Orquesta el flujo completo:

    1. Validación inicial
    2. Corrección automática (si aplica)
    3. Re-validación

    IMPORTANTE:
    - NO sincroniza MySQL
    - La sincronización es responsabilidad de la capa superior (view)

    Garantiza:
    - No marcar como válidos modelos incorrectos
    """

    # =========================
    # ENTRYPOINT
    # =========================

    @classmethod
    def process_model(cls, model: dict):
        """
        Retorna:
        {
            "success": bool,
            "stage": "validation" | "correction",
            "errors": [],
            "changes": [],
            "final_model": {}
        }
        """

        # =========================
        # 1. VALIDACIÓN INICIAL
        # =========================
        validation_1 = ModelValidatorService.validate(model)

        # Si ya es válido → saltar corrección
        if validation_1["is_valid"]:
            corrected_model = model
            changes = []

        else:
            # =========================
            # 2. CORRECCIÓN
            # =========================
            correction = ModelCorrectionService.correct(model)

            corrected_model = correction["corrected_model"]
            changes = correction["changes"]

        # =========================
        # 3. RE-VALIDACIÓN
        # =========================
        validation_2 = ModelValidatorService.validate(corrected_model)

        if not validation_2["is_valid"]:
            return {
                "success": False,
                "stage": "validation",
                "errors": validation_2["errors"],
                "changes": changes,
                "final_model": corrected_model,
            }

        # =========================
        # RESULTADO FINAL (SIN SYNC)
        # =========================
        return {
            "success": True,
            "stage": "correction" if changes else "validation",
            "errors": [],
            "changes": changes,
            "final_model": corrected_model,
        }