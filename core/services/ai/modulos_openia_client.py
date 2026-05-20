import os
import json
from typing import List, Dict, Any
from openai import OpenAI


class OpenAIClient:

    @staticmethod
    def get_client():
        return OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

class AIService:

    @staticmethod
    def _load_system_prompt(filename: str) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No existe el archivo de prompt: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _reducir_modelos(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reduce el tamaño del contexto enviado a la IA"""
        return [
            {
                "nombre": m.get("nombre"),
                "campos": [
                    {
                        "nombre": c.get("nombre"),
                        "tipo": c.get("tipo")
                    }
                    for c in m.get("campos", [])
                ]
            }
            for m in models
        ]

    @staticmethod
    def _validar_campos(campos: Any) -> List[Dict[str, Any]]:
        if not isinstance(campos, list):
            raise ValueError("La respuesta no es una lista")

        required_keys = {"nombre", "tipo", "requerido", "default"}

        for campo in campos:
            if not isinstance(campo, dict):
                raise ValueError(f"Campo no es dict: {campo}")

            if not required_keys.issubset(campo.keys()):
                raise ValueError(f"Campo inválido: {campo}")

        return campos

    @staticmethod
    def interpretar_prompt(prompt, previos, modulo_actual, modules, models):
        client = OpenAIClient.get_client()

        system_prompt = AIService._load_system_prompt("ProtocoloModelosCampos.txt")

        rules_prompt = """
        Reglas:
        - Separar módulos por ingreso independiente
        - Maestro = independiente
        - Cabecera + detalle = transacción
        - Reportes = consultas históricas
        - No unir todo en un módulo
        - Cumplir estructura exacta de JSON
        - Si ya tienes todo, devolver solo JSON válido del modelo del módulo actual
        """

        # 🔥 SOLO enviar nombres de modelos (no todo el payload pesado)
        #modelos_resumen = list(models.keys()) if isinstance(models, dict) else []
        modelos_resumen = []
        models_prompt = "models existentes:\n"
        for model in models:
            models_prompt = models_prompt + f"models: {model['_id']}, Módulo: {model['modulo']}\n"
            if model['modulo'] == modulo_actual:
                tabla = {'nombre': model['_id'], 'campos': []}
                for campo in model['campos']:
                    tabla['campos'].append({
                        "nombre": campo['nombre'],
                        "tipo_base": campo['tipo_base'],
                        "tipo_funcional": campo['tipo_funcional'],
                        "configuracion": campo['configuracion']
                        })
                modelos_resumen.append(tabla)
        models_prompt = "Modelos:\n" + json.dumps(modelos_resumen, ensure_ascii=False)

        user_prompt = f"""
        El usuario solicita: {prompt} sobre el Módulo actual: {modulo_actual}
        """

        respuesa_promt = "se espera de rspuest un JSON con la estrcutura de siguiente estructura:\n"
        respuesa_promt = respuesa_promt + "{'models': actualizado al reuerimeinto del usuario} "

        print('system_prompt:', len(system_prompt))
        print('rules_prompt:', len(rules_prompt))
        print('models_prompt:', len(models_prompt))
        print('respuesa_promt:', len(respuesa_promt))
        print('user_prompt:', len(user_prompt))

        try:
            response = client.responses.create(
                model="gpt-5-mini",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "system", "content": rules_prompt},
                    {"role": "system", "content": models_prompt},
                    {"role": "system", "content": respuesa_promt},                    
                    {"role": "user", "content": user_prompt}
                ]
            )
        except Exception as e:
            raise RuntimeError(f"Error llamando a OpenAI: {str(e)}")

        content = response.output_text.strip()

        # 🔒 Limpieza defensiva
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Respuesta IA inválida:\n{content}")

        # 🔁 Si la IA pide modelos → segundo request con datos filtrados
        if isinstance(parsed, dict) and parsed.get("accion") == "necesita_modelos":
            modelos_solicitados = parsed.get("modelos", [])
            modelos_filtrados = {k: v for k, v in models.items() if k in modelos_solicitados}

            models_prompt_full = "Modelos completos:\n" + json.dumps(modelos_filtrados, ensure_ascii=False, default=str)

            try:
                response = client.responses.create(
                    model="gpt-5-mini",
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "system", "content": rules_prompt},
                        {"role": "system", "content": models_prompt_full},
                        {"role": "user", "content": user_prompt}
                    ]
                )
            except Exception as e:
                raise RuntimeError(f"Error llamando a OpenAI (fase 2): {str(e)}")

            content = response.output_text.strip()

            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()

            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError(f"Respuesta IA inválida (fase 2):\n{content}")

        # 🔧 POST-PROCESO: agregar campos faltantes optimizados
        def completar_campos(modelo):
            for campo in modelo.get("campos", []):
                campo.setdefault("ayuda", "")
                campo.setdefault("placeholder", "")
                campo.setdefault("gap", 0)
                campo.setdefault("gap_top", 0)
            return modelo

        if isinstance(parsed, list):
            parsed = [completar_campos(m) for m in parsed]
        elif isinstance(parsed, dict):
            parsed = completar_campos(parsed)

        return parsed
    

def safe_json(data):
    def converter(o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return str(o)