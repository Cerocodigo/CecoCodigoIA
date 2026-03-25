# core/services/modules/column_comparator_service.py
# ==================================================
# Servicio para comparar columnas MySQL vs definición Mongo→SQL
# ==================================================


class ColumnComparatorService:
    """
    Compara una columna existente en MySQL contra
    una definición generada desde Mongo.

    Evita ALTER TABLE innecesarios.
    """

    # =========================
    # API
    # =========================

    @staticmethod
    def has_changes(mysql_column: dict, mongo_definition: str) -> bool:
        """
        Retorna True si la columna cambió.
        """

        parsed_mysql = ColumnComparatorService._parse_mysql_column(mysql_column)
        parsed_mongo = ColumnComparatorService._parse_definition(mongo_definition)

        return parsed_mysql != parsed_mongo

    # =========================
    # PARSERS
    # =========================

    @staticmethod
    def _parse_mysql_column(row: dict) -> dict:
        """
        Convierte info de information_schema.columns
        a formato comparable
        """

        column_type = row["column_type"].upper()
        is_nullable = row["is_nullable"] == "YES"
        extra = (row.get("extra") or "").upper()

        return {
            "type": column_type,
            "nullable": is_nullable,
            "default": None,  # ⚠️ simplificado (se puede extender luego)
            "extra": extra,
        }

    @staticmethod
    def _parse_definition(definition: str) -> dict:
        """
        Convierte string SQL generado a estructura comparable

        Ejemplo:
        `Secuencial` INT AUTO_INCREMENT PRIMARY KEY NOT NULL
        """

        parts = definition.upper().split()

        # quitar nombre de columna (`campo`)
        parts = parts[1:]

        type_parts = []
        nullable = True
        default = None
        extra_parts = []

        i = 0
        while i < len(parts):
            part = parts[i]

            # NULL / NOT NULL
            if part == "NOT" and i + 1 < len(parts) and parts[i + 1] == "NULL":
                nullable = False
                i += 2
                continue
            elif part == "NULL":
                nullable = True
                i += 1
                continue

            # DEFAULT
            if part == "DEFAULT":
                if i + 1 < len(parts):
                    default = parts[i + 1]
                    i += 2
                    continue

            # PRIMARY KEY / AUTO_INCREMENT
            if part in {"PRIMARY", "KEY", "AUTO_INCREMENT"}:
                extra_parts.append(part)
                i += 1
                continue

            # TYPE (todo lo demás hasta encontrar keywords)
            type_parts.append(part)
            i += 1

        return {
            "type": " ".join(type_parts).strip(),
            "nullable": nullable,
            "default": default,
            "extra": " ".join(extra_parts).strip(),
        }