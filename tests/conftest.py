"""Pruebas de regresión para conftest y sus contratos asociados."""

import os
import sys
import gc
from pathlib import Path

# Asegurar que el root del proyecto esté en sys.path para importar app.*
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from PIL import Image  # noqa: E402
import customtkinter as ctk  # noqa: E402
import tkinter  # noqa: E402


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def fixtures_dir() -> Path:
    return FIXTURES_DIR


def assert_image_size(path: Path, expected_size: tuple[int, int]):
    with Image.open(path) as img:
        assert img.size == expected_size


@pytest.fixture(scope="session")
def tk_session():
    from app.ui import fonts
    fonts.registrar_fuentes()
    try:
        root = ctk.CTk()
    except tkinter.TclError as error:
        if os.environ.get('CI') or os.environ.get('YAGUA_REQUIRE_UI') == '1':
            pytest.fail(f'Tk required for CI tests: {error}')
        pytest.skip(f'Tk no disponible en el entorno de test: {error}')
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture()
def ui_root(tk_session):
    # Se reutiliza un intérprete Tcl y se crea una ventana nueva por prueba, como en la app.
    # Libera ciclos de widgets y fuentes desde el hilo Tk. Si no, un
    # worker de imágenes podría recolectarlos y bloquearse en Font.__del__ esperando
    # el mainloop, mientras las pruebas controlan Tk con update().
    gc.collect()
    root = ctk.CTkToplevel(tk_session)
    root.withdraw()
    yield root
    root.destroy()
    gc.collect()
