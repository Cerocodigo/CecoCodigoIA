# core/services/modules/constants.py
# ==================================================
# Constantes compartidas para módulos dinámicos
# ==================================================

# =========================
# SQL TYPES (Mongo → MySQL)
# =========================
SQL_TYPES_MAP = {
    "pk": "INT AUTO_INCREMENT PRIMARY KEY",
    "string": "VARCHAR(255)",
    "char": "CHAR(1)",
    "text": "TEXT",
    "int": "INT",
    "integer": "INT",
    "decimal": "DECIMAL(10,2)",
    "decimal2": "DECIMAL(10,2)",
    "decimal4": "DECIMAL(10,4)",
    "decimal6": "DECIMAL(10,6)",
    "boolean": "TINYINT(1)",
    "date": "DATE",
    "datetime": "DATETIME",
    "time": "TIME",
    "fk": "INT",
}

# Solo las keys (para validación)
SQL_TYPES_KEYS = set(SQL_TYPES_MAP.keys())


# =========================
# TIPOS FUNCIONALES
# =========================
CECOD_TYPES = {
    "TextoSimple",
    "NumeroSimple",
    "NumeroSecuencial",
    "SistemaFecha",
    "SistemaUsuario",
    "OpcionMultiple",
    "Referencia",
    "ReferenciaBuscador",
    "ReferenciaAdjunto",
    "QueryBaseDatos",
    "Operacion",
    "FormatoTexto",
    "Condicional",
    "Archivo",
    "FormulaDetalle",
    "FechaRegistro",
    "LlaveExterna"
}



# =========================
# CONFIGURACIONES POR TIPO
# (solo estructura esperada)
# =========================
CECOD_CONFIG_STRUCTURE = {
    "TextoSimple": {"unico", "editable", "valor_predeterminado"},
    "NumeroSimple": {"min", "max"},
    "NumeroSecuencial": {"inicio", "incremento"},
    "SistemaFecha": None,
    "SistemaUsuario": {"modo"},
    "OpcionMultiple": {"opciones", "labels", "valor_predeterminado"},
    "Referencia": {
        "sql",
        "label_field",
        "value_field",
        "campo_principal",
        #"campos_filtrables",
        "valor_inicial",
    },
    "ReferenciaBuscador": {
        "sql",
        "value_field",
        "label_field",
        "campos_filtrables",
        "campo_principal",
        "valor_inicial",
        "ModuloIngresoRapido",

    },
    "ReferenciaAdjunto": {"referencia", "campo_origen", "editable"},
    "QueryBaseDatos": {"query", "parametros"},
    "Operacion": {"formula"},
    "FormatoTexto": {"template", "padding"},
    "Condicional": {"condicional"},
    "Archivo": {"acepta_archivo", "tamano_max_mb"},
    "FormulaDetalle": {"operacion", "campo", "tabla", "condicion"},
    "FechaRegistro": {"editable"},
    "LlaveExterna": {"entidad", "campo"},
    
    
}