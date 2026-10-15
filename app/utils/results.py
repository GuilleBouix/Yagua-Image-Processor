"""Per-file failures shared by processing modules and the UI."""
from typing import Literal, TypedDict


class FileFailure(TypedDict):
    ruta: str
    estado: Literal['error']
    motivo: str


def file_failure(path: str, error: object) -> FileFailure:
    return {'ruta': str(path), 'estado': 'error', 'motivo': str(error) or type(error).__name__}
