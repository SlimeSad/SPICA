"""Migración explícita y aditiva; no abre ni busca catálogos operativos."""

import sqlite3

from .modelos import ErrorAlmacenamientoRAW


def migrar_a_v2(conexion: sqlite3.Connection) -> None:
    """El llamador autoriza la conexión. Conserva todas las filas y columnas v1.

    Rechaza transacciones del llamador. Una segunda ejecución sobre v2 es un no-op.
    No asigna metadatos ausentes ni reconstruye identidades.
    """
    if conexion.in_transaction:
        raise ErrorAlmacenamientoRAW("migracion_con_transaccion_activa")
    try:
        conexion.execute("BEGIN IMMEDIATE")
        version = conexion.execute("PRAGMA user_version").fetchone()[0]
        if version == 2:
            conexion.commit()
            return
        if version != 1:
            raise ErrorAlmacenamientoRAW("version_catalogo_no_admitida")
        if conexion.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ErrorAlmacenamientoRAW("relaciones_catalogo_inconsistentes")
        for sentencia in (
            "ALTER TABLE proyectos ADD COLUMN schema_version TEXT",
            "ALTER TABLE proyectos ADD COLUMN nombre TEXT",
            "ALTER TABLE proyectos ADD COLUMN contexto TEXT",
            "ALTER TABLE proyectos ADD COLUMN estado TEXT",
            "ALTER TABLE objetos ADD COLUMN family TEXT",
            "ALTER TABLE objetos ADD COLUMN kind TEXT",
            "ALTER TABLE objetos ADD COLUMN created_at TEXT",
            "ALTER TABLE objetos ADD COLUMN state TEXT",
            "ALTER TABLE activos ADD COLUMN media_detected TEXT",
        ):
            conexion.execute(sentencia)
        if conexion.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ErrorAlmacenamientoRAW("relaciones_catalogo_inconsistentes")
        conexion.execute("PRAGMA user_version=2")
        conexion.commit()
    except BaseException:
        conexion.rollback()
        raise
