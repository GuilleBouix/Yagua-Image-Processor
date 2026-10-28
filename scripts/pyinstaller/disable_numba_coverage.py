"""Desactiva la integración opcional de Numba con coverage en los paquetes de Yagua."""

import sys

sys.modules['coverage'] = None
