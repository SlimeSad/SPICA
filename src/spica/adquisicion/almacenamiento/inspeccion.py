"""Reconocimiento de esquemas RAW conocidos sin escribir en la base inspeccionada."""

from contextlib import closing, contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import tempfile

from .modelos import ErrorAlmacenamientoRAW
from .migraciones import migrar_a_v2
from ._errores import con_limpieza, error_publico


@dataclass(frozen=True)
class PoliticaInspeccionRAW:
    """Presupuesto de copia DB+WAL y margen, no una reserva ni cuota del SO."""
    max_bytes_temporales: int = 512 * 1024**2
    margen_bytes: int = 16 * 1024**2
    tamano_bloque: int = 1_048_576
    directorio_temporal: Path | None = None

    def __post_init__(self):
        for valor in (self.max_bytes_temporales, self.margen_bytes, self.tamano_bloque):
            if type(valor) is not int or valor <= 0:
                raise ValueError("El presupuesto y los bloques deben ser enteros positivos")
        if self.tamano_bloque > 1_048_576 or self.margen_bytes < 65_536:
            raise ValueError("Bloques de hasta 1 MiB y margen de al menos 64 KiB")
        if self.directorio_temporal is not None:
            ruta = Path(self.directorio_temporal).expanduser()
            if not ruta.is_absolute():
                raise ValueError("El directorio temporal debe ser absoluto")
            object.__setattr__(self, "directorio_temporal", ruta)


def _presupuesto(ruta, politica):
    firmas = (_firma(ruta), _firma(Path(str(ruta) + "-wal")))
    if any(f is None for f in firmas):
        raise ErrorAlmacenamientoRAW("catalogo_cambio_durante_inspeccion")
    total = sum(f[2] for f in firmas)
    # El margen incluye SHM y holgura adicional proporcional al tamaño observado.
    necesario = total + politica.margen_bytes + (total + 19) // 20
    if necesario > politica.max_bytes_temporales:
        raise ErrorAlmacenamientoRAW("presupuesto_inspeccion_excedido")
    padre = politica.directorio_temporal or Path(tempfile.gettempdir())
    if (".." in padre.parts or any(p.is_symlink() or p.is_junction() for p in (padre, *padre.parents))
            or not padre.is_dir()):
        raise ErrorAlmacenamientoRAW("directorio_temporal_no_autorizado")
    if shutil.disk_usage(padre).free < necesario:
        raise ErrorAlmacenamientoRAW("espacio_temporal_insuficiente")
    return padre, necesario


# Mismo esquema histórico, sin añadir tablas, columnas ni identificadores nuevos.
SQL_CREAR_V1 = """
CREATE TABLE proyectos (id TEXT PRIMARY KEY);
CREATE TABLE objetos (id TEXT PRIMARY KEY, proyecto_id TEXT NOT NULL REFERENCES proyectos(id));
CREATE TABLE activos (
    id TEXT PRIMARY KEY, objeto_id TEXT NOT NULL REFERENCES objetos(id),
    declaracion TEXT NOT NULL, fecha_utc TEXT NOT NULL,
    estado TEXT NOT NULL CHECK(estado IN ('preparada','verificada_localmente',
      'incorporada','fallida','inconsistente')),
    tamano INTEGER CHECK(tamano >= 0), sha256 TEXT, ruta_interna TEXT,
    error TEXT, advertencias TEXT NOT NULL, comprobacion_utc TEXT);
CREATE TABLE eventos (
    secuencia INTEGER PRIMARY KEY, activo_id TEXT NOT NULL REFERENCES activos(id),
    fecha_utc TEXT NOT NULL, estado TEXT NOT NULL, codigo TEXT);
"""


def _normalizar(sql):
    # Solo reconoce DDL conocido; no intenta interpretar SQL arbitrario equivalente.
    # Conservar íntegros los literales: 'in corporada' NO equivale a 'incorporada'.
    partes = re.split(r"('(?:''|[^'])*'|\"(?:\"\"|[^\"])*\")", sql)
    return "".join(p if i % 2 else re.sub(r"\s+", "", p).casefold()
                   for i, p in enumerate(partes))


def _estructura(conexion):
    resultado = {}
    for tipo, nombre, sql in conexion.execute(
            "SELECT type,name,sql FROM sqlite_master WHERE name NOT GLOB 'sqlite_*' ORDER BY type,name"):
        if tipo == "index":
            # Índices no únicos adicionales no alteran el contrato de integridad.
            tabla = conexion.execute("SELECT tbl_name FROM sqlite_master WHERE type='index' AND name=?", (nombre,)).fetchone()[0]
            if tabla not in {"proyectos", "objetos", "activos", "eventos"}:
                raise ErrorAlmacenamientoRAW("catalogo_ajeno")
            if any(f[1] == nombre and f[2] for f in conexion.execute(f'PRAGMA index_list("{tabla}")')):
                raise ErrorAlmacenamientoRAW("estructura_catalogo_no_reconocida")
            continue
        if tipo != "table" or nombre not in {"proyectos", "objetos", "activos", "eventos"}:
            raise ErrorAlmacenamientoRAW("catalogo_ajeno")
        resultado[nombre] = (
            tuple(conexion.execute(f"PRAGMA table_info({nombre})")),
            tuple(sorted(conexion.execute(f"PRAGMA foreign_key_list({nombre})"))),
            _normalizar(sql),
        )
    return resultado


@lru_cache(maxsize=2)
def _esperada(version):
    with closing(sqlite3.connect(":memory:")) as c:
        c.executescript(SQL_CREAR_V1 + "PRAGMA user_version=1;")
        if version == 2:
            migrar_a_v2(c)  # Solo la referencia vacía en memoria.
        return _estructura(c)


def _validar_conexion(conexion):
    version = conexion.execute("PRAGMA user_version").fetchone()[0]
    app = conexion.execute("PRAGMA application_id").fetchone()[0]
    if app != 0 or version == 0:
        raise ErrorAlmacenamientoRAW("catalogo_ajeno")
    if version not in (1, 2):
        raise ErrorAlmacenamientoRAW("version_catalogo_no_admitida")
    real = _estructura(conexion)
    # Compatibilidad histórica: v1 puede contener todas las columnas aditivas v2,
    # pero sigue siendo v1 y sus APIs MD siguen exigiendo migración explícita.
    candidatas = (_esperada(1), _esperada(2)) if version == 1 else (_esperada(2),)
    if real not in candidatas:
        raise ErrorAlmacenamientoRAW("estructura_catalogo_no_reconocida")
    if conexion.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ErrorAlmacenamientoRAW("relaciones_catalogo_inconsistentes")
    if conexion.execute("PRAGMA quick_check(1)").fetchone() != ("ok",):
        raise ErrorAlmacenamientoRAW("integridad_catalogo_no_comprobada")
    return version


def _firma(ruta):
    try:
        s = ruta.stat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(s.st_mode):
        raise ErrorAlmacenamientoRAW("catalogo_o_auxiliar_no_regular")
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


@contextmanager
def _lectura_sqlite(ruta, hay_wal, politica):
    if not hay_wal:
        # immutable evita recuperación/escritura de diarios o archivos auxiliares.
        with closing(sqlite3.connect(ruta.as_uri() + "?mode=ro&immutable=1", uri=True)) as c:
            yield c
        return
    # Un lector WAL convencional puede crear/tocar -shm incluso con mode=ro.
    # Copiar DB y WAL a un temporal privado permite interpretar commits sin tocar
    # el diario ni el índice WAL originales. No se copian originales científicos.
    padre, necesario = _presupuesto(ruta, politica)
    principal = None
    creado = False
    try:
        with tempfile.TemporaryDirectory(prefix="spica-inspeccion-sqlite-", dir=padre) as temporal:
            creado = True
            try:
                if shutil.disk_usage(temporal).free < necesario:
                    raise ErrorAlmacenamientoRAW("espacio_temporal_insuficiente")
                copia = Path(temporal) / "catalogo.sqlite3"
                copiados = 0
                for original, destino in ((ruta, copia), (Path(str(ruta) + "-wal"), Path(str(copia) + "-wal"))):
                    firma = _firma(original)
                    if firma is None:
                        raise ErrorAlmacenamientoRAW("catalogo_cambio_durante_inspeccion")
                    with original.open("rb") as entrada, destino.open("xb") as salida:
                        restantes = firma[2]
                        while restantes:
                            bloque = entrada.read(min(restantes, politica.tamano_bloque))
                            if not bloque:
                                raise ErrorAlmacenamientoRAW("catalogo_cambio_durante_inspeccion")
                            copiados += len(bloque)
                            if copiados + politica.margen_bytes + (copiados + 19) // 20 > politica.max_bytes_temporales:
                                raise ErrorAlmacenamientoRAW("presupuesto_inspeccion_excedido")
                            if salida.write(bloque) != len(bloque):
                                raise ErrorAlmacenamientoRAW("copia_inspeccion_incompleta")
                            restantes -= len(bloque)
                    if _firma(original) != firma:
                        raise ErrorAlmacenamientoRAW("catalogo_cambio_durante_inspeccion")
                with closing(sqlite3.connect(copia.as_uri() + "?mode=ro", uri=True)) as c:
                    yield c
            except BaseException as error:
                principal = error
    except OSError:
        if not creado:
            raise
        if principal is None:
            principal = ErrorAlmacenamientoRAW("limpieza_inspeccion_incompleta")
        con_limpieza(principal, (("snapshot_sqlite", "eliminacion_no_disponible"),))
    if principal is not None:
        raise principal


@error_publico("inspeccion_sqlite", "inspeccion_catalogo_no_disponible", "inspeccion_catalogo_no_disponible")
def inspeccionar_catalogo(ruta: Path, *, politica: PoliticaInspeccionRAW | None = None) -> int:
    """Devuelve 1/2 solo para una estructura RAW reconocida. Nunca crea la ruta.

    Reconocimiento estructural, no prueba criptográfica de origen. Requiere que no
    haya escritores durante la inspección; detecta cambios ordinarios mediante stat.
    """
    ruta = Path(ruta).absolute()
    politica = politica or PoliticaInspeccionRAW()
    try:
        if ".." in ruta.parts or any(p.is_symlink() or p.is_junction() for p in (ruta, *ruta.parents)):
            raise ErrorAlmacenamientoRAW("ruta_catalogo_no_autorizada")
        firma = _firma(ruta)
        if firma is None:
            raise ErrorAlmacenamientoRAW("catalogo_no_encontrado")
        if firma[2] == 0:
            raise ErrorAlmacenamientoRAW("catalogo_vacio_no_reconocido")
        ruta = ruta.resolve(strict=True)
        wal = Path(str(ruta) + "-wal")
        journal = Path(str(ruta) + "-journal")
        for auxiliar in (wal, journal, Path(str(ruta) + "-shm")):
            if auxiliar.is_symlink() or auxiliar.is_junction():
                raise ErrorAlmacenamientoRAW("auxiliar_catalogo_no_autorizado")
            _firma(auxiliar)  # Rechaza auxiliares no regulares sin abrirlos.
        if _firma(journal) is not None:
            raise ErrorAlmacenamientoRAW("diario_rollback_requiere_revision")
        firma_wal = _firma(wal)
        with _lectura_sqlite(ruta, firma_wal is not None and firma_wal[2] > 0, politica) as conexion:
            conexion.execute("PRAGMA query_only=ON")
            conexion.execute("PRAGMA trusted_schema=OFF")
            version = _validar_conexion(conexion)
        if _firma(ruta) != firma or _firma(wal) != firma_wal or _firma(journal) is not None:
            raise ErrorAlmacenamientoRAW("catalogo_cambio_durante_inspeccion")
        return version
    except (OSError, sqlite3.Error) as error:
        raise con_limpieza(ErrorAlmacenamientoRAW("inspeccion_catalogo_no_disponible"),
                           getattr(error, "fallos_limpieza", ())) from None
