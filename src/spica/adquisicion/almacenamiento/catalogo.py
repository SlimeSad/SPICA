"""Catálogo SQLite y transiciones persistentes cortas; no mueve archivos."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from ..nucleo import Fuente
from .modelos import (ActivoRAW, DeclaracionRAW, EstadoIncorporacion, ErrorAlmacenamientoRAW,
                      ObjetoCientifico, ProyectoCientifico)
from .migraciones import migrar_a_v2
from .inspeccion import SQL_CREAR_V1, inspeccionar_catalogo


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


class CatalogoRAW:
    def __init__(self, ruta: Path, *, politica_inspeccion=None):
        ruta = Path(ruta).absolute()
        nuevo = False
        if ruta.exists():
            inspeccionar_catalogo(ruta, politica=politica_inspeccion)
        else:
            if any(Path(str(ruta) + sufijo).exists() for sufijo in ("-wal", "-shm", "-journal")):
                raise ErrorAlmacenamientoRAW("auxiliares_sin_catalogo_requieren_revision")
            # La creación es exclusiva y distinta de la inspección. Un archivo
            # vacío preexistente no se adopta como un catálogo nuevo.
            with ruta.open("xb"):
                pass
            nuevo = True
        # mode=rw evita crear otra base si desaparece la ruta tras la inspección.
        self.conexion = sqlite3.connect(ruta.resolve().as_uri() + "?mode=rw", uri=True, timeout=5)
        self.conexion.row_factory = sqlite3.Row
        try:
            self.conexion.execute("PRAGMA foreign_keys=ON")
            self.conexion.execute("PRAGMA synchronous=FULL")
            if nuevo:
                self.conexion.execute("PRAGMA journal_mode=DELETE")
                self.conexion.executescript("BEGIN IMMEDIATE;" + SQL_CREAR_V1
                                           + "PRAGMA user_version=1;COMMIT;")
                # Solo el catálogo recién creado, sin datos, evoluciona automáticamente.
                migrar_a_v2(self.conexion)
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
            self.conexion.execute("INSERT OR IGNORE INTO proyectos(id) VALUES (?)", (declaracion.proyecto_id,))
            self.conexion.execute("INSERT OR IGNORE INTO objetos(id,proyecto_id) VALUES (?,?)",
                                  (declaracion.objeto_id, declaracion.proyecto_id))
            proyecto = self.conexion.execute("SELECT proyecto_id FROM objetos WHERE id=?",
                                             (declaracion.objeto_id,)).fetchone()[0]
            if proyecto != declaracion.proyecto_id:
                raise ErrorAlmacenamientoRAW("objeto_de_otro_proyecto")
            self.conexion.execute("""INSERT INTO activos(id,objeto_id,declaracion,fecha_utc,estado,
                tamano,sha256,ruta_interna,error,advertencias,comprobacion_utc)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
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
                         datetime.fromisoformat(fila["comprobacion_utc"]) if fila["comprobacion_utc"] else None,
                         fila["media_detected"] if "media_detected" in fila.keys() else None)

    def listar(self) -> tuple[ActivoRAW, ...]:
        return tuple(self.consultar(fila[0]) for fila in self.conexion.execute("SELECT id FROM activos ORDER BY fecha_utc,id").fetchall())

    def consultar_proyecto(self, project_id: str) -> ProyectoCientifico:
        fila = self.conexion.execute("SELECT * FROM proyectos WHERE id=?", (project_id,)).fetchone()
        if fila is None:
            raise ErrorAlmacenamientoRAW("proyecto_no_encontrado")
        return ProyectoCientifico(fila["id"], **{k: fila[k] if k in fila.keys() else None
            for k in ("schema_version", "nombre", "contexto", "estado")})

    def consultar_objeto(self, object_id: str) -> ObjetoCientifico:
        fila = self.conexion.execute("SELECT * FROM objetos WHERE id=?", (object_id,)).fetchone()
        if fila is None:
            raise ErrorAlmacenamientoRAW("objeto_no_encontrado")
        datos = {k: fila[k] if k in fila.keys() else None for k in ("family", "kind", "created_at", "state")}
        if datos["created_at"] is not None:
            datos["created_at"] = datetime.fromisoformat(datos["created_at"])
        return ObjetoCientifico(fila["id"], fila["proyecto_id"], **datos)

    def _exigir_v2(self):
        if self.conexion.execute("PRAGMA user_version").fetchone()[0] != 2:
            raise ErrorAlmacenamientoRAW("migracion_explicita_requerida")

    def registrar_proyecto(self, proyecto: ProyectoCientifico) -> ProyectoCientifico:
        self._exigir_v2()
        with self.conexion:
            self.conexion.execute("INSERT OR IGNORE INTO proyectos(id) VALUES (?)", (proyecto.project_id,))
            anterior = self.consultar_proyecto(proyecto.project_id)
            campos = ("schema_version", "nombre", "contexto", "estado")
            if any(getattr(anterior, c) is not None and getattr(proyecto, c) is not None
                   and getattr(anterior, c) != getattr(proyecto, c) for c in campos):
                raise ErrorAlmacenamientoRAW("metadatos_proyecto_en_conflicto")
            self.conexion.execute("""UPDATE proyectos SET schema_version=COALESCE(schema_version,?),
                nombre=COALESCE(nombre,?),contexto=COALESCE(contexto,?),estado=COALESCE(estado,?) WHERE id=?""",
                (proyecto.schema_version, proyecto.nombre, proyecto.contexto, proyecto.estado, proyecto.project_id))
        return self.consultar_proyecto(proyecto.project_id)

    def registrar_objeto(self, objeto: ObjetoCientifico) -> ObjetoCientifico:
        self._exigir_v2()
        with self.conexion:
            self.consultar_proyecto(objeto.project_id)
            self.conexion.execute("INSERT OR IGNORE INTO objetos(id,proyecto_id) VALUES (?,?)",
                                  (objeto.object_id, objeto.project_id))
            anterior = self.consultar_objeto(objeto.object_id)
            if anterior.project_id != objeto.project_id:
                raise ErrorAlmacenamientoRAW("objeto_de_otro_proyecto")
            campos = ("family", "kind", "created_at", "state")
            if any(getattr(anterior, c) is not None and getattr(objeto, c) is not None
                   and getattr(anterior, c) != getattr(objeto, c) for c in campos):
                raise ErrorAlmacenamientoRAW("metadatos_objeto_en_conflicto")
            self.conexion.execute("""UPDATE objetos SET family=COALESCE(family,?),kind=COALESCE(kind,?),
                created_at=COALESCE(created_at,?),state=COALESCE(state,?) WHERE id=?""", (
                objeto.family, objeto.kind,
                objeto.created_at.astimezone(timezone.utc).isoformat() if objeto.created_at else None,
                objeto.state, objeto.object_id))
        return self.consultar_objeto(objeto.object_id)
