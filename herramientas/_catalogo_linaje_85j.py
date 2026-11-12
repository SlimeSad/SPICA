"""Extensión 85001 exclusivamente de catálogos sintéticos nuevos del piloto 85-J.

Reutiliza el DDL v1 existente; no altera el lector estable ni migra bases del usuario.
"""

from contextlib import closing
import sqlite3

from spica.adquisicion.catalogo import CatalogoCientifico

VERSION_SQLITE = 85001
VERSION_FORMATO = "0.1.0"
_DDL = """
CREATE TABLE linaje_instancia (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    instancia_id TEXT NOT NULL UNIQUE, version TEXT NOT NULL CHECK(version='0.1.0'));
CREATE TABLE linaje_ejecuciones (
    ejecucion_id TEXT PRIMARY KEY NOT NULL,
    conservacion_id TEXT NOT NULL UNIQUE,
    estado_historico TEXT NOT NULL CHECK(estado_historico IN
        ('concluida_estructuralmente','incompleta','fallida','cancelada')),
    estado TEXT NOT NULL CHECK(estado IN
        ('preparada','escribiendo','publicada','referencias_confirmadas','conservada','incompleta','fallida')),
    contexto_sha256 TEXT NOT NULL CHECK(length(contexto_sha256)=64),
    manifiesto_sha256 TEXT CHECK(length(manifiesto_sha256)=64),
    creada_utc TEXT NOT NULL);
CREATE TABLE linaje_artefactos (
    ejecucion_id TEXT NOT NULL REFERENCES linaje_ejecuciones(ejecucion_id),
    rol TEXT NOT NULL CHECK(rol IN ('informe','traza','referencia','manifiesto')),
    sha256 TEXT NOT NULL CHECK(length(sha256)=64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    tamano INTEGER NOT NULL CHECK(tamano>0),
    PRIMARY KEY(ejecucion_id,rol));
CREATE TABLE linaje_eventos (
    secuencia INTEGER PRIMARY KEY,
    ejecucion_id TEXT NOT NULL REFERENCES linaje_ejecuciones(ejecucion_id),
    estado TEXT NOT NULL, codigo TEXT NOT NULL, fecha_utc TEXT NOT NULL);
"""


class ErrorIndice85J(ValueError):
    pass


def _estructura(c):
    return tuple((n, t, " ".join(sql.split()) if sql else None) for n, t, sql in
                 c.execute("SELECT name,type,sql FROM sqlite_master ORDER BY name"))


def _esperada(version):
    with closing(sqlite3.connect(":memory:")) as c:
        # Acoplamiento privado acotado a la herramienta experimental, bajo pruebas.
        CatalogoCientifico._crear(None, conexion=c)
        if version == VERSION_SQLITE:
            c.executescript(_DDL)
        return _estructura(c), c.execute("PRAGMA application_id").fetchone()[0]


def validar(c, version=VERSION_SQLITE):
    if c.execute("PRAGMA user_version").fetchone()[0] != version:
        raise ErrorIndice85J("version_sqlite_incompatible")
    estructura, app = _esperada(version)
    if c.execute("PRAGMA application_id").fetchone()[0] != app or _estructura(c) != estructura:
        raise ErrorIndice85J("estructura_sqlite_incompatible")
    if c.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ErrorIndice85J("referencias_sqlite_inconsistentes")
    if c.execute("PRAGMA quick_check(1)").fetchone()[0] != "ok":
        raise ErrorIndice85J("sqlite_inconsistente")
    if version == VERSION_SQLITE:
        if c.execute("SELECT count(*) FROM linaje_instancia").fetchone()[0] != 1:
            raise ErrorIndice85J("instancia_sqlite_ausente")


def crear_nuevo(ruta, instancia):
    """Solo se llama dentro de una raíz recién creada exclusivamente por el piloto."""
    with ruta.open("xb"):
        pass
    with CatalogoCientifico(ruta):
        pass
    with closing(sqlite3.connect(ruta)) as c:
        validar(c, 1)
        # Ni siquiera se permite extender una base v1 que contenga metadatos.
        for tabla in ("fuentes", "productos", "estaciones", "variables", "disponibilidades", "capacidades", "revisiones"):
            if c.execute(f"SELECT 1 FROM {tabla} LIMIT 1").fetchone():
                raise ErrorIndice85J("origen_sqlite_no_vacio")
        try:
            c.executescript("BEGIN IMMEDIATE;" + _DDL)
            c.execute("INSERT INTO linaje_instancia VALUES (1,?,?)", (instancia, VERSION_FORMATO))
            c.execute(f"PRAGMA user_version={VERSION_SQLITE}")
            c.commit()
        except BaseException:
            c.rollback()
            raise
        validar(c)


def abrir(ruta, *, lectura=False):
    # DELETE es el perfil admitido: no interpretar un hot journal o WAL como vacío.
    if any(ruta.with_name(ruta.name + suf).exists() for suf in ("-wal", "-shm", "-journal")):
        raise ErrorIndice85J("auxiliares_sqlite_requieren_revision")
    uri = ruta.as_uri() + ("?mode=ro&immutable=1" if lectura else "?mode=rw")
    c = sqlite3.connect(uri, uri=True, timeout=1)
    try:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA trusted_schema=OFF")
        if lectura:
            c.execute("PRAGMA query_only=ON")
        else:
            c.execute("PRAGMA synchronous=FULL")
        validar(c)
        return c
    except BaseException:
        c.close()
        raise
