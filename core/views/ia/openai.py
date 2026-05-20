import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def interpretar_prompt(prompt, campos_actuales):
    """
    prompt: str (ej: 'agregar campo precio_unitario decimal obligatorio')
    campos_actuales: list[dict] (estructura actual del modelo)
    return: list{dict} (estructura ajustada)
    """

    system_prompt = """
Eres un asistente que modifica estructuras de formularios dinámicos.
REGLAS IMPORTANTES:
- Responde SOLO con JSON válido
- No expliques nada
- No incluyas texto fuera del JSON
- Mantén los campos existentes
- Solo modifica lo que el usuario pide
- Usa este formato de campo:

{
  "nombre": "precio_unitario",
  "tipo": "decimal|texto|numero|fecha|boolean",
  "requerido": true,
  "default": null
}
"""

    user_prompt = f"""
Campos actuales:
{json.dumps(campos_actuales, ensure_ascii=False, indent=2)}

Instrucción del usuario:
{prompt}

Devuelve el JSON actualizado de los campos.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    content = response.choices[0].message.content.strip()

    # 🔒 Seguridad mínima
    try:
        campos_nuevos = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Respuesta IA inválida: {content}")

    return campos_nuevos