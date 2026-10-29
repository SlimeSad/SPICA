"""Fronteras técnicas RAW: publicar códigos, nunca excepciones del backend."""

from functools import wraps
import sqlite3

from .modelos import ErrorAlmacenamientoRAW


class ErrorOperacionRAW(ErrorAlmacenamientoRAW):
    def __init__(self, codigo, fase, fallos_limpieza=()):
        super().__init__(codigo)
        self.fase = fase
        self.estado = ("no_inicializado" if codigo == "almacen_raw_no_inicializado"
                       else "revision_necesaria")
        # Pares (rol técnico, código); sin rutas, documentos ni objetos originales.
        self.fallos_limpieza = tuple(fallos_limpieza)

    def diagnostico_publico(self):
        return dict(codigo=self.codigo, fase=self.fase, estado=self.estado,
                    fallos_limpieza=self.fallos_limpieza)


def _publicar(error):
    # Quitar también el contexto que Python añade desde el llamador activo.
    try:
        raise error from None
    except Exception:
        error.__cause__ = None
        error.__context__ = None
        raise


def error_publico(fase, permisos, fallo):
    """Conserva la compatibilidad con ErrorAlmacenamientoRAW en cada frontera."""
    def decorar(funcion):
        @wraps(funcion)
        def ejecutar(*args, **kwargs):
            try:
                return funcion(*args, **kwargs)
            except ErrorAlmacenamientoRAW as interno:
                publico = ErrorOperacionRAW(interno.codigo, fase,
                                            getattr(interno, "fallos_limpieza", ()))
            except PermissionError as interno:
                publico = ErrorOperacionRAW(permisos, fase,
                                            getattr(interno, "fallos_limpieza", ()))
            except (OSError, sqlite3.Error) as interno:
                publico = ErrorOperacionRAW(fallo, fase,
                                            getattr(interno, "fallos_limpieza", ()))
            _publicar(publico)
        return ejecutar
    return decorar


def con_limpieza(error, fallos):
    error.fallos_limpieza = getattr(error, "fallos_limpieza", ()) + tuple(fallos)
    return error
