import os
import json
import google.generativeai as genai
from typing import Dict, Any

class GeminiConnector:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Inicializa la conexión con Gemini.
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            # Forzamos al modelo a que siempre responda en formato JSON
            generation_config={"response_mime_type": "application/json"}
        )

    def enviar_peticion_json(self, prompt: str, schema: str = "") -> Dict[str, Any]:
        """
        Envía un prompt y espera una respuesta JSON. 
        Opcionalmente se puede pasar un esquema para guiar al modelo.
        """
        try:
            # Si se proporciona un esquema, se añade al prompt para mayor precisión
            full_prompt = prompt
            if schema:
                full_prompt += f"\n\nResponde siguiendo estrictamente este esquema JSON: {schema}"

            response = self.model.generate_content(full_prompt)
            
            # Convertimos el texto de la respuesta (string) a un diccionario de Python
            return json.loads(response.text)
            
        except Exception as e:
            return {"error": f"Error al procesar la solicitud: {str(e)}"}

# --- Ejemplo de uso ---

if __name__ == "__main__":
    # Sustituye con tu API KEY real
    MI_API_KEY = "AIzaSyAHuq4pInifptNnuR444OFR6OXk5PAlPdw"
    
    gemini = GeminiConnector(api_key=MI_API_KEY)

    # Definimos qué queremos y qué estructura esperamos
    mi_prompt = "Dime los beneficios de comer manzanas y naranjas."
    mi_esquema = """
    {
      "frutas": [
        {"nombre": "string", "beneficios": ["string", "string"]}
      ]
    }
    """

    resultado = gemini.enviar_peticion_json(mi_prompt, mi_esquema)
    
    # Imprimir el resultado de forma legible
    print(json.dumps(resultado, indent=4, ensure_ascii=False))