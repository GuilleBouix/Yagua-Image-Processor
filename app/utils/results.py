"""Estructura de fallos por archivo compartida entre módulos de proceso e interfaz."""
from typing import Literal, TypedDict


class FileFailure(TypedDict):
    """Describe la ruta que falló y el motivo que se puede presentar al usuario."""
    ruta: str
    estado: Literal['error']
    motivo: str


def file_failure(path: str, error: object) -> FileFailure:
    """Normaliza una excepción en el formato común de fallos por archivo."""
    return {'ruta': str(path), 'estado': 'error', 'motivo': str(error) or type(error).__name__}
