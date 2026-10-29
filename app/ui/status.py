"""Resúmenes breves de operaciones, sin cifras técnicas ni contadores vacíos."""
from app.translations import t


def operation_summary(count, errors=0, *, action='saved', unchanged=0, skipped=0):
    """Muestra únicamente las cantidades que explican el resultado al usuario."""
    parts = [t('status_' + key).format(count=value) for key, value in (
        (action, count), ('unchanged', unchanged), ('omitted', skipped), ('errors', errors)) if value]
    return ' · '.join(parts) if parts else t('status_empty')
