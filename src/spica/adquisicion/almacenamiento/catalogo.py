"""Catálogo SQLite y transiciones persistentes cortas; no mueve archivos."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from ..nucleo import Fuente
from .modelos import ActivoRAW, DeclaracionRAW, EstadoIncorporacion, ErrorAlmacenamientoRAW


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


class CatalogoRAW:
    def __init__(self, ruta: Path):
        self.conexion = sqlite3.connect(ruta, timeout=5)
        self.conexion.row_factory = sqlite3.Row
        try:
            self.conexion.execute("PRAGMA foreign_keys=ON")
            self.conexion.execute("PRAGMA synchronous=FULL")
            self.conexion.execute("PRAGMA journal_mode=DELETE")
            version = self.conexion.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ErrorAlmacenamientoRAW("version_catalogo_no_admitida")
            if version == 0:
                if self.conexion.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                    raise ErrorAlmacenamientoRAW("catalogo_ajeno")
                self.conexion.executescript("""
                    BEGIN IMMEDIATE;
                    CREATE TABLE proyectos (id TEXT PRIMARY KEY);
                    CREATE TABLE objetos (id TEXT PRIMARY KEY, proyecto_id TEXT NOT NULL REFERENCES proyectos(id));
                    CREATE TABLE activos (
                        id TEXT PRIMARY KEY, objeto_id TEXT NOT NULL REFERENCES objetos(id),
                        declaracion TEXT NOT NULL, fecha_utc TEXT NOT NULL,
                        estado TEXT NOT NULL CHECK(estado IN ('preparada','verificada_localmente',
                          'incorporada','fallida','inconsistente')),
                        tamano INTEGER CHECK(tamano >= 0), sha256 TEXT, ruta_interna TEXT,
                        error TEXT, advertencias TEXT NOT NULL, comprobacion_utc TEXT
                    );
                    CREATE TABLE eventos (
                        secuencia INTEGER PRIMARY KEY, activo_id TEXT NOT NULL REFERENCES activos(id),
                        fecha_utc TEXT NOT NULL, estado TEXT NOT NULL, codigo TEXT
                    );
                    PRAGMA user_version=1;
                    COMMIT;
                """)
        except BaseException:
            self.conexion.close()
            raise

    def close(self):
        self.conexion.close()

    def preparar(self, activo_id: str, declaracion: DeclaracionRAW, advertencias: tuple[str, ...]):
        contenido = dict(proyecto_id=declaracion.proyecto_id, objeto_id=declaracion.objeto_id,
                         fuente=dict(proveedor=declaracion.fuente.proveedor,
                                     identificador=declaracion.fuente.identificador),
                         recurso_id=declaracion.recurso_id, procedencia=declaracion.procedencia,
                         parametros_publicos=dict(declaracion.parametros_publicos),
                         formato_declarado=declaracion.formato_declarado,
                         tipo_medio_declarado=declaracion.tipo_medio_declarado)
        with self.conexion:
            self.conexion.execute("INSERT OR IGNORE INTO proyectos VALUES (?)", (declaracion.proyecto_id,))
            self.conexion.execute("INSERT OR IGNORE INTO objetos VALUES (?,?)",
                                  (declaracion.objeto_id, declaracion.proyecto_id))
            proyecto = self.conexion.execute("SELECT proyecto_id FROM objetos WHERE id=?",
                                             (declaracion.objeto_id,)).fetchone()[0]
            if proyecto != declaracion.proyecto_id:
                raise ErrorAlmacenamientoRAW("objeto_de_otro_proyecto")
            self.conexion.execute("INSERT INTO activos VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
                activo_id, declaracion.objeto_id, json.dumps(contenido, ensure_ascii=False), ahora(),
                EstadoIncorporacion.PREPARADA.value, None, None, None, None,
                json.dumps(advertencias), None))
            self._evento(activo_id, EstadoIncorporacion.PREPARADA, None)

    def _evento(self, activo_id, estado, codigo):
        self.conexion.execute("INSERT INTO eventos(activo_id,fecha_utc,estado,codigo) VALUES (?,?,?,?)",
                              (activo_id, ahora(), estado.value, codigo))

    def transicion(self, activo_id: str, estado: EstadoIncorporacion, *, tamano=None, sha256=None,
                   ruta=None, error=None, comprobacion=None):
        with self.conexion:
            self.conexion.execute("""UPDATE activos SET estado=?, tamano=COALESCE(?,tamano),
                sha256=COALESCE(?,sha256), ruta_interna=COALESCE(?,ruta_interna), error=?,
                comprobacion_utc=COALESCE(?,comprobacion_utc) WHERE id=?""", (
                estado.value, tamano, sha256, ruta, error, comprobacion, activo_id))
            self._evento(activo_id, estado, error)

    def consultar(self, activo_id: str) -> ActivoRAW:
        fila = self.conexion.execute("SELECT * FROM activos WHERE id=?", (activo_id,)).fetchone()
        if fila is None:
            raise ErrorAlmacenamientoRAW("activo_no_encontrado", activo_id)
        datos = json.loads(fila["declaracion"])
        datos["fuente"] = Fuente(**datos["fuente"])
        return ActivoRAW(fila["id"], DeclaracionRAW(**datos), datetime.fromisoformat(fila["fecha_utc"]),
                         EstadoIncorporacion(fila["estado"]), fila["tamano"], fila["sha256"],
                         fila["ruta_interna"], fila["error"], tuple(json.loads(fila["advertencias"])),
                         datetime.fromisoformat(fila["comprobacion_utc"]) if fila["comprobacion_utc"] else None)

    def listar(self) -> tuple[ActivoRAW, ...]:
        return tuple(self.consultar(fila[0]) for fila in self.conexion.execute("SELECT id FROM activos ORDER BY fecha_utc,id").fetchall())
