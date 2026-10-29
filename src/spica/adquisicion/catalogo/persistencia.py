"""Catálogo de descubrimiento independiente de SQLite RAW; sin acceso a la red."""

from contextlib import closing
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..almacenamiento.raw import _referencia_publica, _segura
from ..almacenamiento import ErrorAlmacenamientoRAW
from ..nucleo import Fuente
from ..nucleo.temporal import instante_utc
from .modelos import (
    CapacidadCatalogo, CoincidenciaTemporal, DisponibilidadCatalogo, EntidadCatalogo,
    ErrorCatalogo, EstacionCatalogo, EstadoVerificacion, EvaluacionDisponibilidad,
    FiltroCatalogo, FuenteCatalogo, MecanismoAdquisicion, ProcedenciaCatalogo,
    ProductoCatalogo, RegistroCatalogo, ResultadoCatalogo, ResultadoProducto, VariableCatalogo,
)

_APLICACION = 0x53554341
_TABLAS = {FuenteCatalogo: "fuentes", ProductoCatalogo: "productos", EstacionCatalogo: "estaciones",
           VariableCatalogo: "variables", DisponibilidadCatalogo: "disponibilidades", CapacidadCatalogo: "capacidades"}
_CLASES = {v: k for k, v in _TABLAS.items()}


def _datos(valor):
    if isinstance(valor, datetime):
        datos = {"__fecha__": valor.isoformat()}
        if valor.fold:
            datos["__fold__"] = valor.fold
        if isinstance(valor.tzinfo, ZoneInfo):
            if not valor.tzinfo.key:
                raise ErrorCatalogo("zona_temporal_sin_identificador_persistible")
            datos.update(__zona__=valor.tzinfo.key, __fold__=valor.fold,
                         __nombre_zona__=valor.tzname())
            # Una clave de ZoneInfo.from_file no garantiza que pueda reabrirse.
            # Comprobar antes de escribir evita guardar una fila ilegible.
            _fecha_persistida(datos)
        elif isinstance(valor.tzinfo, timezone):
            if valor.tzname() != datetime.fromisoformat(valor.isoformat()).tzname():
                datos["__nombre_zona__"] = valor.tzname()
        elif valor.tzinfo is not None:
            raise ErrorCatalogo("tipo_zona_temporal_no_persistible")
        return datos
    if isinstance(valor, Enum):
        return valor.value
    if is_dataclass(valor):
        return {c.name: _datos(getattr(valor, c.name)) for c in fields(valor)}
    if isinstance(valor, tuple):
        return [_datos(v) for v in valor]
    return valor


def _publico(valor):
    if isinstance(valor, str):
        # Reutiliza el filtro conservador existente; no sanea IDs destructivamente.
        try:
            _referencia_publica(valor, sanear_url=False)
        except ErrorAlmacenamientoRAW:
            raise ErrorCatalogo("metadato_no_publico_o_ambiguo") from None
    elif is_dataclass(valor):
        for c in fields(valor):
            _publico(getattr(valor, c.name))
    elif isinstance(valor, tuple):
        for elemento in valor:
            _publico(elemento)


def _fecha_persistida(dato):
    if "__fecha__" not in dato:
        return dato
    try:
        if not set(dato) <= {"__fecha__", "__fold__", "__zona__", "__nombre_zona__"}:
            raise ValueError
        fecha = datetime.fromisoformat(dato["__fecha__"])
        fold = dato.get("__fold__", 0)
        if type(fold) is not int or fold not in (0, 1):
            raise ValueError
        fecha = fecha.replace(fold=fold)
        if "__zona__" in dato:
            # No sustituir una zona ausente o cuyas reglas cambiaron por UTC.
            zona = ZoneInfo(dato["__zona__"])
            original = fecha.replace(tzinfo=zona)
            if (original.utcoffset() != fecha.utcoffset()
                    or original.tzname() != dato.get("__nombre_zona__")):
                raise ValueError
            instante_utc(original)
            return original
        if "__nombre_zona__" in dato:
            fecha = fecha.replace(tzinfo=timezone(fecha.utcoffset(), dato["__nombre_zona__"]))
        return fecha
    except (ValueError, TypeError, OverflowError, ZoneInfoNotFoundError):
        raise ErrorCatalogo("fecha_o_zona_persistida_no_reconstruible") from None


def _leer_json(texto):
    return json.loads(texto, object_hook=_fecha_persistida)


def _entidad(tabla, contenido):
    datos = _leer_json(contenido)
    datos["fuente"] = Fuente(**datos["fuente"])
    datos["procedencia"] = ProcedenciaCatalogo(**datos["procedencia"])
    if "estado" in datos:
        datos["estado"] = EstadoVerificacion(datos["estado"])
    if "mecanismo" in datos:
        datos["mecanismo"] = MecanismoAdquisicion(datos["mecanismo"])
    return _CLASES[tabla](**datos)


def _columnas(entidad):
    datos = {"proveedor": entidad.fuente.proveedor, "fuente_id": entidad.fuente.identificador}
    if not isinstance(entidad, FuenteCatalogo):
        datos["producto_id"] = entidad.identificador if isinstance(entidad, ProductoCatalogo) else entidad.producto_id
    if isinstance(entidad, (EstacionCatalogo, DisponibilidadCatalogo, CapacidadCatalogo)):
        datos["identificador"] = entidad.identificador
    if isinstance(entidad, VariableCatalogo):
        datos.update(id_interno=entidad.id_interno, codigo_original=entidad.codigo_original)
    if isinstance(entidad, DisponibilidadCatalogo):
        datos.update(estacion_id=entidad.estacion_id, variable_id=entidad.variable_id)
    if isinstance(entidad, CapacidadCatalogo):
        datos["mecanismo"] = entidad.mecanismo.value
    return datos


def _clave(entidad):
    columnas = _columnas(entidad)
    if isinstance(entidad, VariableCatalogo):
        return {"id_interno": entidad.id_interno}
    return {k: v for k, v in columnas.items() if k in ("proveedor", "fuente_id", "producto_id", "identificador")}


class CatalogoCientifico:
    def __init__(self, ruta: Path):
        ruta = _segura(ruta)
        _segura(ruta.parent).resolve(strict=True)
        self._conexion = sqlite3.connect(ruta, timeout=5)
        self._conexion.row_factory = sqlite3.Row
        try:
            app = self._conexion.execute("PRAGMA application_id").fetchone()[0]
            version = self._conexion.execute("PRAGMA user_version").fetchone()[0]
            tablas = self._conexion.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if not tablas and app == 0 and version == 0:
                self._crear()
            elif app != _APLICACION or version != 1:
                raise ErrorCatalogo("catalogo_ajeno_o_version_no_admitida")
            self._validar_estructura()
            self._conexion.execute("PRAGMA foreign_keys=ON")
            self._conexion.execute("PRAGMA synchronous=FULL")
        except BaseException:
            self._conexion.close()
            raise

    def _validar_estructura(self):
        """No adoptar una base incompleta por compartir application_id/version."""
        def estructura(conexion):
            return tuple((n, t, " ".join(sql.split()) if sql else None) for n, t, sql in
                conexion.execute("SELECT name,type,sql FROM sqlite_master ORDER BY name"))
        # Se reutiliza el mismo DDL en memoria; no se migra ni escribe la base
        # inspeccionada y se comprueban también CHECK, PK, FK, índices y triggers.
        with closing(sqlite3.connect(":memory:")) as memoria:
            self._crear(conexion=memoria)
            esperada = estructura(memoria)
        if estructura(self._conexion) != esperada:
            raise ErrorCatalogo("estructura_catalogo_no_admitida")
        if self._conexion.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ErrorCatalogo("relaciones_catalogo_inconsistentes")

    def _crear(self, *, conexion=None):
        (conexion if conexion is not None else self._conexion).executescript(f"""
            BEGIN IMMEDIATE;
            CREATE TABLE fuentes (
                proveedor TEXT NOT NULL, fuente_id TEXT NOT NULL,
                contenido TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
                PRIMARY KEY(proveedor,fuente_id));
            CREATE TABLE productos (
                proveedor TEXT NOT NULL, fuente_id TEXT NOT NULL, producto_id TEXT NOT NULL,
                contenido TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
                PRIMARY KEY(proveedor,fuente_id,producto_id),
                FOREIGN KEY(proveedor,fuente_id) REFERENCES fuentes(proveedor,fuente_id));
            CREATE TABLE estaciones (
                proveedor TEXT NOT NULL, fuente_id TEXT NOT NULL, producto_id TEXT NOT NULL,
                identificador TEXT NOT NULL, contenido TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
                PRIMARY KEY(proveedor,fuente_id,producto_id,identificador),
                FOREIGN KEY(proveedor,fuente_id,producto_id) REFERENCES productos(proveedor,fuente_id,producto_id));
            CREATE TABLE variables (
                id_interno TEXT PRIMARY KEY NOT NULL, proveedor TEXT NOT NULL, fuente_id TEXT NOT NULL,
                producto_id TEXT NOT NULL, codigo_original TEXT, contenido TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK(revision>0),
                UNIQUE(proveedor,fuente_id,producto_id,codigo_original),
                UNIQUE(proveedor,fuente_id,producto_id,id_interno),
                FOREIGN KEY(proveedor,fuente_id,producto_id) REFERENCES productos(proveedor,fuente_id,producto_id));
            CREATE TABLE disponibilidades (
                proveedor TEXT NOT NULL, fuente_id TEXT NOT NULL, producto_id TEXT NOT NULL,
                identificador TEXT NOT NULL, estacion_id TEXT, variable_id TEXT,
                contenido TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
                PRIMARY KEY(proveedor,fuente_id,producto_id,identificador),
                FOREIGN KEY(proveedor,fuente_id,producto_id) REFERENCES productos(proveedor,fuente_id,producto_id),
                FOREIGN KEY(proveedor,fuente_id,producto_id,estacion_id)
                    REFERENCES estaciones(proveedor,fuente_id,producto_id,identificador),
                FOREIGN KEY(proveedor,fuente_id,producto_id,variable_id)
                    REFERENCES variables(proveedor,fuente_id,producto_id,id_interno));
            CREATE TABLE capacidades (
                proveedor TEXT NOT NULL, fuente_id TEXT NOT NULL, producto_id TEXT NOT NULL,
                identificador TEXT NOT NULL, mecanismo TEXT NOT NULL, contenido TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK(revision>0),
                PRIMARY KEY(proveedor,fuente_id,producto_id,identificador),
                FOREIGN KEY(proveedor,fuente_id,producto_id) REFERENCES productos(proveedor,fuente_id,producto_id));
            CREATE TABLE revisiones (
                secuencia INTEGER PRIMARY KEY, tabla TEXT NOT NULL, clave TEXT NOT NULL,
                revision INTEGER NOT NULL, contenido TEXT NOT NULL, registrada_utc TEXT NOT NULL,
                motivo TEXT NOT NULL, UNIQUE(tabla,clave,revision));
            PRAGMA application_id={_APLICACION};
            PRAGMA user_version=1;
            COMMIT;
        """)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._conexion.close()

    def _fila(self, tabla, clave):
        condicion = " AND ".join(f"{k}=?" for k in clave)
        return self._conexion.execute(f"SELECT * FROM {tabla} WHERE {condicion}", tuple(clave.values())).fetchone()

    def _consultar(self, tabla, clave):
        fila = self._fila(tabla, clave)
        if fila is None:
            raise ErrorCatalogo("metadato_no_identificado")
        return RegistroCatalogo(_entidad(tabla, fila["contenido"]), fila["revision"])

    def consultar_fuente(self, fuente: Fuente):
        return self._consultar("fuentes", {"proveedor": fuente.proveedor, "fuente_id": fuente.identificador})

    def consultar_producto(self, fuente: Fuente, producto_id: str):
        return self._consultar("productos", dict(proveedor=fuente.proveedor, fuente_id=fuente.identificador, producto_id=producto_id))

    def consultar_estacion(self, fuente: Fuente, producto_id: str, estacion_id: str):
        return self._consultar("estaciones", dict(proveedor=fuente.proveedor, fuente_id=fuente.identificador,
                                                 producto_id=producto_id, identificador=estacion_id))

    def consultar_variable(self, id_interno: str):
        return self._consultar("variables", {"id_interno": id_interno})

    def consultar_disponibilidad(self, fuente: Fuente, producto_id: str, identificador: str):
        return self._consultar("disponibilidades", dict(proveedor=fuente.proveedor, fuente_id=fuente.identificador,
                                                      producto_id=producto_id, identificador=identificador))

    def consultar_capacidad(self, fuente: Fuente, producto_id: str, identificador: str):
        return self._consultar("capacidades", dict(proveedor=fuente.proveedor, fuente_id=fuente.identificador,
                                                 producto_id=producto_id, identificador=identificador))

    def _relaciones(self, entidad):
        if isinstance(entidad, (EstacionCatalogo, DisponibilidadCatalogo)):
            producto = self.consultar_producto(entidad.fuente, entidad.producto_id).entidad
            tiene_estacion = isinstance(entidad, EstacionCatalogo) or entidad.estacion_id is not None
            if producto.utiliza_estaciones is False and tiene_estacion:
                raise ErrorCatalogo("producto_sin_estaciones")
        if isinstance(entidad, ProductoCatalogo) and entidad.utiliza_estaciones is False:
            columnas = _clave(entidad)
            if self._conexion.execute("SELECT 1 FROM estaciones WHERE proveedor=? AND fuente_id=? AND producto_id=?",
                                      tuple(columnas.values())).fetchone():
                raise ErrorCatalogo("producto_con_estaciones_registradas")

    def registrar(self, entidad: EntidadCatalogo) -> RegistroCatalogo:
        return self._guardar(entidad, None, "registro_inicial")

    def registrar_documental(self, entidad):
        """Política optativa; registrar()/actualizar() conservan sus contratos."""
        from .documental import registrar_documental
        return registrar_documental(self, entidad)

    def consultar_recurso(self, fuente: Fuente, producto_id: str, recurso_id: str, *, revision=None):
        from .documental import consultar_recurso
        return consultar_recurso(self, fuente, producto_id, recurso_id, revision)

    def listar_recursos(self, fuente: Fuente, producto_id: str):
        from .documental import consultar_recurso
        claves = self._conexion.execute("SELECT DISTINCT clave FROM revisiones WHERE tabla='recursos' ORDER BY clave")
        return tuple(consultar_recurso(self, fuente, producto_id, clave["identificador"])
                     for fila in claves for clave in (json.loads(fila[0]),)
                     if (clave["proveedor"], clave["fuente_id"], clave["producto_id"])
                     == (fuente.proveedor, fuente.identificador, producto_id))

    def consultar_revision(self, entidad, revision: int):
        from .documental import RecursoCatalogo, _clave_recurso, consultar_revision
        if isinstance(entidad, RecursoCatalogo):
            tabla = "recursos"
            clave = _clave_recurso(entidad.fuente, entidad.producto_id, entidad.identificador)
        else:
            tabla, clave = _TABLAS[type(entidad)], _clave(entidad)
        return consultar_revision(self, tabla, clave, revision)

    def actualizar(self, entidad: EntidadCatalogo, *, revision_esperada: int, motivo: str) -> RegistroCatalogo:
        if type(revision_esperada) is not int or revision_esperada <= 0 or not isinstance(motivo, str) or not motivo.strip():
            raise ValueError("Se requiere revisión esperada positiva y motivo")
        _publico(motivo)
        return self._guardar(entidad, revision_esperada, motivo)

    def _guardar(self, entidad, esperada, motivo, *, transaccion_externa=False):
        if type(entidad) not in _TABLAS:
            raise TypeError("Entidad de catálogo no admitida")
        _publico(entidad)
        tabla = _TABLAS[type(entidad)]
        clave = _clave(entidad)
        contenido = json.dumps(_datos(entidad), ensure_ascii=False, sort_keys=True)
        propia = not transaccion_externa
        try:
            # Control optimista de revisión bajo bloqueo de escritura SQLite.
            if propia:
                self._conexion.execute("BEGIN IMMEDIATE")
            fila = self._fila(tabla, clave)
            if fila is not None and esperada is None:
                if fila["contenido"] != contenido:
                    raise ErrorCatalogo("registro_contradictorio_requiere_revision")
                if propia:
                    self._conexion.rollback()
                return RegistroCatalogo(entidad, fila["revision"])
            if esperada is not None:
                if fila is None or fila["revision"] != esperada:
                    raise ErrorCatalogo("revision_obsoleta_o_registro_no_identificado")
                anterior = _entidad(tabla, fila["contenido"])
                if _columnas(anterior) != _columnas(entidad):
                    # Mecanismo puede revisarse; identidad y vínculos no.
                    a, b = _columnas(anterior), _columnas(entidad)
                    a.pop("mecanismo", None)
                    b.pop("mecanismo", None)
                    if a != b:
                        raise ErrorCatalogo("identidad_o_vinculo_no_modificable")
                if entidad.procedencia.revisada_utc <= anterior.procedencia.revisada_utc:
                    raise ErrorCatalogo("procedencia_de_revision_no_posterior")
            self._relaciones(entidad)
            columnas = _columnas(entidad)
            revision = 1 if fila is None else fila["revision"] + 1
            if fila is None:
                valores = dict(columnas, contenido=contenido, revision=revision)
                self._conexion.execute(f"INSERT INTO {tabla} ({','.join(valores)}) VALUES ({','.join('?' for _ in valores)})",
                                       tuple(valores.values()))
            else:
                valores = dict(columnas, contenido=contenido, revision=revision)
                self._conexion.execute(f"UPDATE {tabla} SET {','.join(k+'=?' for k in valores)} WHERE "
                                       + " AND ".join(k+"=?" for k in clave), tuple(valores.values()) + tuple(clave.values()))
            self._conexion.execute("INSERT INTO revisiones(tabla,clave,revision,contenido,registrada_utc,motivo) VALUES (?,?,?,?,?,?)",
                (tabla, json.dumps(clave, sort_keys=True), revision, contenido, datetime.now(timezone.utc).isoformat(), motivo))
            if propia:
                self._conexion.commit()
        except sqlite3.IntegrityError:
            if propia:
                self._conexion.rollback()
            raise ErrorCatalogo("relacion_o_identificador_invalido") from None
        except BaseException:
            if propia:
                self._conexion.rollback()
            raise
        return RegistroCatalogo(entidad, revision)

    def historial(self, entidad: EntidadCatalogo) -> tuple[RegistroCatalogo, ...]:
        tabla = _TABLAS[type(entidad)]
        filas = self._conexion.execute("SELECT contenido,revision FROM revisiones WHERE tabla=? AND clave=? ORDER BY revision",
            (tabla, json.dumps(_clave(entidad), sort_keys=True))).fetchall()
        return tuple(RegistroCatalogo(_entidad(tabla, f["contenido"]), f["revision"]) for f in filas)

    def _listar(self, tabla):
        return tuple(_entidad(tabla, f[0]) for f in self._conexion.execute(f"SELECT contenido FROM {tabla} ORDER BY rowid"))

    def leer_acotado(self, filtro: FiltroCatalogo, *, max_registros: int,
                     max_bytes: int) -> tuple[RegistroCatalogo, ...]:
        """Instantánea limitada para planificación; solo filtra fuente/producto.

        Cuenta registros y bytes UTF-8 antes de deserializar. No modifica el
        esquema ni descarta evidencia por filtros de estación, tiempo o frecuencia.
        """
        if not isinstance(filtro, FiltroCatalogo):
            raise TypeError("Se requiere FiltroCatalogo")
        if any(type(v) is not int or v <= 0 for v in (max_registros, max_bytes)):
            raise ValueError("Limites positivos requeridos")
        tablas = ("productos", "estaciones", "variables", "disponibilidades", "capacidades")
        condiciones, valores = [], []
        if filtro.fuentes:
            condiciones.append("(" + " OR ".join("(proveedor=? AND fuente_id=?)" for _ in filtro.fuentes) + ")")
            for fuente in filtro.fuentes:
                valores.extend((fuente.proveedor, fuente.identificador))
        if filtro.productos:
            condiciones.append("producto_id IN (" + ",".join("?" for _ in filtro.productos) + ")")
            valores.extend(filtro.productos)
        donde = " WHERE " + " AND ".join(condiciones) if condiciones else ""
        if self._conexion.in_transaction:
            raise ErrorCatalogo("lectura_acotada_requiere_conexion_sin_transaccion")
        self._conexion.execute("BEGIN")
        try:
            cantidad = volumen = 0
            for tabla in tablas:
                n, b = self._conexion.execute(
                    f"SELECT count(*),coalesce(sum(length(CAST(contenido AS BLOB))),0) FROM {tabla}" + donde,
                    valores).fetchone()
                cantidad += n
                volumen += b
                if cantidad > max_registros or volumen > max_bytes:
                    raise ErrorCatalogo("limite_lectura_catalogo_excedido")
            registros = []
            for tabla in tablas:
                for fila in self._conexion.execute(
                        f"SELECT contenido,revision FROM {tabla}" + donde + " ORDER BY contenido", valores):
                    registros.append(RegistroCatalogo(_entidad(tabla, fila["contenido"]), fila["revision"]))
            return tuple(registros)
        finally:
            self._conexion.rollback()

    def listar(self, tipo: type, *, fuente: Fuente | None = None,
               producto_id: str | None = None) -> tuple[RegistroCatalogo, ...]:
        """Explora metadatos registrados; una colección vacía no prueba ausencia de datos."""
        if tipo not in _TABLAS:
            raise TypeError("Tipo de entidad no admitido")
        resultado = []
        for entidad in self._listar(_TABLAS[tipo]):
            if fuente is not None and entidad.fuente != fuente:
                continue
            producto = entidad.identificador if isinstance(entidad, ProductoCatalogo) else getattr(entidad, "producto_id", None)
            if producto_id is not None and producto != producto_id:
                continue
            resultado.append(self._consultar(_TABLAS[tipo], _clave(entidad)))
        return tuple(resultado)

    def buscar(self, filtro: FiltroCatalogo = FiltroCatalogo()) -> ResultadoCatalogo:
        if not isinstance(filtro, FiltroCatalogo):
            raise TypeError("Se requiere FiltroCatalogo")
        disponibilidades = self._listar("disponibilidades")
        capacidades = self._listar("capacidades")
        variables = {v.id_interno: v for v in self._listar("variables")}
        resultados = []
        for producto in self._listar("productos"):
            if filtro.fuentes and producto.fuente not in filtro.fuentes:
                continue
            if filtro.productos and producto.identificador not in filtro.productos:
                continue
            if filtro.estaciones and producto.utiliza_estaciones is False:
                continue
            capacidades_producto = tuple(c for c in capacidades if (c.fuente, c.producto_id) == (producto.fuente, producto.identificador))
            compatibles = tuple(c for c in capacidades_producto if not filtro.mecanismos or c.mecanismo in filtro.mecanismos)
            evaluaciones = []
            for registro in disponibilidades:
                if (registro.fuente, registro.producto_id) != (producto.fuente, producto.identificador):
                    continue
                if filtro.estaciones and registro.estacion_id is not None and registro.estacion_id not in filtro.estaciones:
                    continue
                if filtro.variables and registro.variable_id is not None and registro.variable_id not in filtro.variables:
                    continue
                codigo = variables[registro.variable_id].codigo_original if registro.variable_id is not None else None
                if filtro.codigos_variables and codigo is not None and codigo not in filtro.codigos_variables:
                    continue
                if filtro.frecuencias and registro.frecuencia_declarada is not None and registro.frecuencia_declarada not in filtro.frecuencias:
                    continue
                alcance = not ((filtro.estaciones and registro.estacion_id is None)
                               or (filtro.variables and registro.variable_id is None)
                               or (filtro.codigos_variables and codigo is None)
                               or (filtro.frecuencias and registro.frecuencia_declarada is None))
                evaluaciones.append(EvaluacionDisponibilidad(registro, _temporal(registro, filtro), alcance))
            resultados.append(ResultadoProducto(producto, tuple(evaluaciones), compatibles,
                not any(e.alcance_exacto and e.disponibilidad.estado is not EstadoVerificacion.DESCONOCIDO
                        for e in evaluaciones), not compatibles))
        return ResultadoCatalogo(filtro, tuple(resultados))


def _temporal(registro, filtro):
    if filtro.inicio is None:
        return CoincidenciaTemporal.SIN_FILTRO
    if registro.estado is EstadoVerificacion.DESCONOCIDO:
        return CoincidenciaTemporal.DESCONOCIDA
    limites = (registro.inicio, registro.fin)
    if any(d is not None and d.utcoffset() is None for d in limites):
        return CoincidenciaTemporal.DESCONOCIDA
    inicio = instante_utc(registro.inicio) if registro.inicio is not None else None
    fin = instante_utc(registro.fin) if registro.fin is not None else None
    si, sf = instante_utc(filtro.inicio), instante_utc(filtro.fin)
    if ((fin is not None and fin < si) or (inicio is not None and inicio > sf)):
        return CoincidenciaTemporal.FUERA_COBERTURA_CONOCIDA
    if registro.inicio is None or registro.fin is None:
        return CoincidenciaTemporal.DESCONOCIDA
    if inicio <= si and fin >= sf:
        return CoincidenciaTemporal.CONTIENE_PERIODO
    return CoincidenciaTemporal.SOLAPAMIENTO_PARCIAL
