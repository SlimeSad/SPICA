"""Evidencia de fixtures en un temporal privado, con limpieza al salir del contexto."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Iterator

from .modelos import ResultadoEnsayo


class ErrorEvidenciaEnsayo(RuntimeError):
    """Código fijo, sin mensajes del sistema ni cuerpos o rutas de usuario."""


@dataclass(frozen=True)
class EvidenciaTemporal:
    directorio: Path = field(repr=False)
    registro: Path = field(repr=False)
    cuerpo: Path | None = field(repr=False)
    sha256_registro: str
    cuerpo_verificado_fisicamente: bool
    verificado_utc: datetime


def _base_temporal():
    base = Path(tempfile.gettempdir())
    # Rechazar antes de stat/resolve: nunca inspeccionar un almacén operativo.
    def protegida(p):
        s = os.path.normcase(os.path.abspath(str(p)))
        raw = os.path.normcase(os.path.abspath(str(Path.home() / "SPICA_DATOS")))
        codigo = os.path.normcase(str(Path(__file__).absolute().parents[4]))
        return (s == raw or s.startswith(raw + os.sep)
                or s == codigo or s.startswith(codigo + os.sep)
                or any(x.lower() in (".git", ".venv") for x in p.parts))
    if base.drive.startswith("\\\\") or not base.is_absolute() or protegida(base):
        raise ErrorEvidenciaEnsayo("base_temporal_no_admitida")
    for p in (base, *base.parents):
        if p.is_symlink() or p.is_junction():
            raise ErrorEvidenciaEnsayo("base_temporal_con_enlace")
    resuelta = base.resolve(strict=True)
    if protegida(resuelta) or not resuelta.is_dir():
        raise ErrorEvidenciaEnsayo("base_temporal_no_admitida")
    return resuelta


def _registro(resultado, verificado_utc, cuerpo_verificado):
    p = resultado.solicitud.preparacion
    return {
        "version_registro_sintetico": "0.1", "procedencia": resultado.procedencia,
        "ensayo_id": p.ensayo_id,
        "candidato_solo_declarativo": {
            "institucion_objetivo": p.institucion_objetivo, "producto_objetivo": p.producto_objetivo,
            "servicio": p.servicio, "capa_id": p.capa_id, "capa_nombre": p.capa_nombre,
            "metodo_previsto": p.metodo_previsto, "url_candidata": p.url_candidata,
            "autorizacion": p.autorizacion.value, "max_bytes": p.max_bytes,
            "max_entidades": p.max_entidades, "permitir_geometrias": p.permitir_geometrias,
        },
        "solicitud_exacta_simulada": {
            "destino": resultado.solicitud.destino, "metodo_simulado": p.metodo_previsto,
            "parametros": dict(p.parametros),
        },
        "evaluado_utc": resultado.evaluado_utc.isoformat(), "estado": resultado.estado.value,
        "recepcion": resultado.recepcion.value, "validacion": resultado.validacion.value,
        "sintaxis_completa": resultado.sintaxis_completa,
        "codigo_http_sintetico": resultado.codigo_http, "respuesta_id": resultado.respuesta_id,
        "operaciones_simuladas": resultado.operaciones_simuladas,
        "bytes_observados": resultado.bytes_observados, "longitud_declarada": resultado.longitud_declarada,
        "sha256_bytes_sinteticos": resultado.sha256,
        "oid_observados_en_fixture": [e.object_id_observado for e in resultado.entidades],
        "capa_observada_en_fixture": resultado.capa_observada,
        "exceededTransferLimit": resultado.exceeded_transfer_limit,
        "precision": resultado.precision.value,
        "completitud_institucional": resultado.completitud_institucional.value,
        "capacidad_institucional_demostrada": False, "tls_ejercido": False,
        "diagnosticos": list(resultado.diagnosticos), "restricciones": list(resultado.restricciones),
        "motivos_detencion_previstos": list(p.motivos_detencion),
        "archivo_cuerpo": "respuesta.bin" if resultado.contenido is not None else None,
        "comprobacion_temporal_utc": verificado_utc.isoformat(),
        "bytes_disponibles_verificados_fisicamente": cuerpo_verificado,
    }


@contextmanager
def conservar_evidencia(resultado: ResultadoEnsayo) -> Iterator[EvidenciaTemporal]:
    """Sin argumento de destino: no puede publicar en RAW ni sobrescribir originales.

    Los archivos solo existen durante el contexto. La comprobación es de bytes
    sintéticos disponibles, incluso parciales; no confirma una transferencia o RAW.
    """
    if type(resultado) is not ResultadoEnsayo:
        raise TypeError("resultado_sintetico_tipificado_requerido")
    contenido = resultado.contenido
    if contenido is not None:
        if (len(contenido) != resultado.bytes_observados
                or hashlib.sha256(contenido).hexdigest() != resultado.sha256):
            raise ErrorEvidenciaEnsayo("resultado_y_bytes_incoherentes")
    elif resultado.sha256 is not None:
        raise ErrorEvidenciaEnsayo("hash_sin_bytes_disponibles")
    try:
        base = _base_temporal()
        with tempfile.TemporaryDirectory(prefix="spica-piloto-arcgis-sintetico-", dir=base) as nombre:
            directorio = Path(nombre)
            cuerpo = None
            if contenido is not None:
                cuerpo = directorio / "respuesta.bin"
                with cuerpo.open("xb") as f:
                    f.write(contenido)
                releido = cuerpo.read_bytes()  # Cierre y reapertura reales, solo de la fixture.
                if releido != contenido or hashlib.sha256(releido).hexdigest() != resultado.sha256:
                    raise ErrorEvidenciaEnsayo("comprobacion_fisica_sintetica_fallida")
            verificado_utc = datetime.now(timezone.utc)
            registro = directorio / "registro.json"
            datos = json.dumps(_registro(resultado, verificado_utc, cuerpo is not None),
                               ensure_ascii=True, sort_keys=True, indent=2).encode("utf-8")
            if len(datos) > 32_768:
                raise ErrorEvidenciaEnsayo("limite_registro_sintetico_excedido")
            with registro.open("xb") as f:
                f.write(datos)
            observado = registro.read_bytes()
            if observado != datos:
                raise ErrorEvidenciaEnsayo("comprobacion_registro_fallida")
            yield EvidenciaTemporal(directorio, registro, cuerpo, hashlib.sha256(observado).hexdigest(),
                                    cuerpo is not None, verificado_utc)
    except OSError:
        raise ErrorEvidenciaEnsayo("error_evidencia_temporal_sintetica") from None
