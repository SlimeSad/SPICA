"""Agregados efímeros, acotados y descartables. Nunca abre un catálogo RAW."""

import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from uuid import uuid4


class LimitePerfil(Exception):
    """Solo códigos propios constantes, sin textos de backend o rutas."""


class IndicePerfil:
    def __init__(self, ruta_fuente, limites, directorio_temporal):
        self.ruta_fuente, self.p = Path(ruta_fuente).absolute(), limites
        self.padre = (Path(directorio_temporal) if directorio_temporal is not None
                      else Path(tempfile.gettempdir()).resolve())
        self.carpeta = self.conexion = None
        self.creada = False
        self.eliminado = True
        self.claves = dict(horas=0, dias=0, periodos=0, valores=0)

    def abrir(self):
        padre = self.padre
        if (not padre.is_absolute() or ".." in padre.parts or not padre.is_dir()
                or any(q.is_symlink() or q.is_junction() for q in (padre, *padre.parents))
                or padre.resolve().is_relative_to(self.ruta_fuente.parent)):
            raise LimitePerfil("directorio_temporal_no_admitido")
        if shutil.disk_usage(padre).free < self.p.max_bytes_indice + 2 * 1024**2:
            raise LimitePerfil("espacio_temporal_insuficiente")
        self.carpeta = padre / ("spica-perfil-" + uuid4().hex)
        self.carpeta.mkdir(mode=0o755 if os.name == "nt" else 0o700)
        self.creada, self.eliminado = True, False
        c = self.conexion = sqlite3.connect(self.carpeta / "indice.sqlite3")
        c.execute("PRAGMA page_size=4096")
        c.execute(f"PRAGMA max_page_count={self.p.max_bytes_indice // 4096}")
        c.execute("PRAGMA cache_size=-1024")
        c.execute("PRAGMA journal_mode=OFF")
        c.execute("PRAGMA synchronous=OFF")
        c.execute("PRAGMA temp_store=MEMORY")
        c.execute("PRAGMA trusted_schema=OFF")
        for tabla, columnas in (("horas", "estacion,fecha,hora"),
                                ("periodos", "estacion,mes,hora"),
                                ("valores", "estacion,variable,literal")):
            ddl = ",".join(f"{nombre} TEXT NOT NULL" for nombre in columnas.split(","))
            c.execute(f"CREATE TABLE {tabla} ({ddl},n INTEGER NOT NULL,PRIMARY KEY ({columnas})) WITHOUT ROWID")
        c.execute("CREATE TABLE dias (estacion TEXT,fecha TEXT,n INTEGER,horas INTEGER,"
                  "PRIMARY KEY (estacion,fecha)) WITHOUT ROWID")

    def contar(self, tabla, clave, limite):
        columnas = {"horas": ("estacion", "fecha", "hora"),
                    "periodos": ("estacion", "mes", "hora"),
                    "valores": ("estacion", "variable", "literal")}[tabla]
        donde = " AND ".join(f"{col}=?" for col in columnas)
        c = self.conexion
        previo = c.execute(f"SELECT n FROM {tabla} WHERE {donde}", clave).fetchone()
        if previo is None:
            if self.claves[tabla] >= limite:
                raise LimitePerfil("limite_claves_" + tabla)
            c.execute(f"INSERT INTO {tabla} VALUES (?,?,?,1)", clave)
            self.claves[tabla] += 1
        else:
            c.execute(f"UPDATE {tabla} SET n=n+1 WHERE {donde}", clave)
        return previo is None

    def registrar(self, estacion, fecha_literal, hora, dia, valores):
        nueva = self.contar("horas", (estacion, fecha_literal, hora), self.p.max_claves_hora)
        if dia is not None:
            fecha = dia.isoformat()
            c = self.conexion
            previo = c.execute("SELECT n FROM dias WHERE estacion=? AND fecha=?", (estacion, fecha)).fetchone()
            if previo is None:
                if self.claves["dias"] >= self.p.max_dias:
                    raise LimitePerfil("limite_claves_dias")
                c.execute("INSERT INTO dias VALUES (?,?,1,1)", (estacion, fecha))
                self.claves["dias"] += 1
            else:
                c.execute("UPDATE dias SET n=n+1,horas=horas+? WHERE estacion=? AND fecha=?",
                          (int(nueva), estacion, fecha))
            self.contar("periodos", (estacion, fecha[:7], hora), self.p.max_claves_periodo)
        for variable, valor in valores:
            if valor != "":
                self.contar("valores", (estacion, variable, valor), self.p.max_valores_distintos)

    def cerrar(self):
        try:
            if self.conexion is not None:
                self.conexion.close()
        finally:
            if self.creada:
                (self.carpeta / "indice.sqlite3").unlink(missing_ok=True)
                self.carpeta.rmdir()  # No borrado recursivo ni objetos ajenos.
                self.eliminado = True
