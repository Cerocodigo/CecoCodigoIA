# core/services/modules/mongo_to_mysql_field_mapper.py
# ==================================================
# Conversión de campos MongoDB → definición SQL MySQL
# (Versión alineada a nueva estandarización)
# ==================================================

from core.services.modules.constants import SQL_TYPE_META


def mongo_field_to_sql(campo: dict) -> str:
    """
    Convierte un campo del modelo MongoDB
    a definición SQL MySQL.

    REGLAS:
    - Solo depende de tipo_base (NO tipo_funcional)
    - pk ya viene definido en SQL_TYPES_MAP
    - requerido define NULL / NOT NULL
    - valor_default se respeta si existe
    """

    nombre = campo["nombre"]
    nombre_sql = f"`{nombre}`"

    tipo_base = campo.get("tipo_base")
    meta = SQL_TYPE_META.get(tipo_base)

    if not meta:
        raise ValueError(f"Tipo SQL no soportado: {tipo_base}")

    sql_type = meta["sql"]

    if not sql_type:
        raise ValueError(f"Tipo SQL no soportado: {tipo_base}")

    # =========================
    # NULL / NOT NULL
    # =========================
    requerido = campo.get("requerido", False)

    # PK siempre NOT NULL (aunque ya viene en definición)
    if tipo_base == "pk":
        null_sql = "NOT NULL"
    else:
        null_sql = "NOT NULL" if requerido else "NULL"

    # =========================
    # DEFAULT
    # =========================
    default_sql = ""

    valor_default = campo.get("valor_default")

    if valor_default is not None and tipo_base != "pk":
        default_sql = _build_default_sql(valor_default, tipo_base)

    # =========================
    # RESULTADO FINAL
    # =========================
    parts = [
        nombre_sql,
        sql_type,
        null_sql,
    ]

    if default_sql:
        parts.append(default_sql)

    return " ".join(parts).strip()


# ==================================================
# HELPERS
# ==================================================

def _build_default_sql(valor, tipo_base):
    """
    Construye correctamente el DEFAULT según tipo
    """

    # Strings / fechas → comillas
    if tipo_base in {"string", "char", "text", "date", "datetime", "time"}:
        return f"DEFAULT '{valor}'"

    # Boolean → 1 o 0
    if tipo_base == "boolean":
        return f"DEFAULT {1 if valor else 0}"

    # Numéricos
    if tipo_base in {"int", "integer", "decimal2", "decimal4", "decimal6", "fk"}:
        return f"DEFAULT {valor}"

    # fallback
    return f"DEFAULT '{valor}'"