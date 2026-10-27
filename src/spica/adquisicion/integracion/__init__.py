"""Coordinación experimental entre transporte y almacenamiento; sin conectores."""

from .http_raw import AdaptadorHTTPRAW, ErrorIntegracionHTTPRAW, FaseHTTPRAW, ResultadoHTTPRAW

__all__ = ["AdaptadorHTTPRAW", "ErrorIntegracionHTTPRAW", "FaseHTTPRAW", "ResultadoHTTPRAW"]
