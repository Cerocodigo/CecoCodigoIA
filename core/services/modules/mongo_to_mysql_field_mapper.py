# core/services/modules/mongo_to_mysql_field_mapper.py
# ==================================================
# Conversión de campos MongoDB → definición SQL MySQL
# ==================================================


SQL_TYPES = {
    "string": "VARCHAR(255)",
    "char": "CHAR(1)",
    "text": "TEXT",
    "int": "INT",
    "integer": "INT",
    "decimal": "DECIMAL(10,2)",
    "boolean": "TINYINT(1)",
    "date": "DATE",
    "datetime": "DATETIME",
    "time": "TIME",
    "fk": "INT",
}


def mongo_field_to_sql(campo: dict) -> str:
    """
    Convierte un campo del modelo MongoDB
    a definición SQL MySQL.
    """

    nombre = campo["nombre"]
    nombre_sql = f"`{nombre}`"

    tipo_base = campo.get("tipo_base")
    tipo_funcional = campo.get("tipo_funcional")

    sql_type = SQL_TYPES.get(tipo_base)
    if not sql_type:
        raise ValueError(f"Tipo SQL no soportado: {tipo_base}")

    requerido = campo.get("requerido", False)
    null_sql = "NOT NULL" if requerido else "NULL"

    extras = []

    if tipo_funcional == "NumeroSecuencial":
        extras.append("AUTO_INCREMENT")
        extras.append("PRIMARY KEY")
        null_sql = "NOT NULL"

    if tipo_funcional == "FechaCreacion":
        extras.append("DEFAULT CURRENT_TIMESTAMP")

    if tipo_funcional == "FechaActualizacion":
        extras.append(
            "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )

    return " ".join([
        nombre_sql,
        sql_type,
        null_sql,
        *extras
    ]).strip()
