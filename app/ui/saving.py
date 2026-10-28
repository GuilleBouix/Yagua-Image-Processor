"""Controles de guardado compartidos y confirmación asíncrona del destino."""
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.translations import t
from app.ui import colors, fonts
from app.ui.image_cache import image_cache
from app.utils.saving import plan_outputs


def selector_steps(view, parent, row, *, columnspan=1, padx=16):
    """Crea pasos de interfaz para construir el selector de salida."""
    if not hasattr(view, '_save_choice'):
        view._save_choice = ctk.StringVar(value=t('save_copies'))
    box = ctk.CTkFrame(parent, fg_color='transparent')
    box.grid(row=row, column=0, columnspan=columnspan, padx=padx, pady=(8, 12), sticky='ew')
    box.grid_columnconfigure(1, weight=1)
    view._save_groups = [*getattr(view, '_save_groups', []), box]
    if not view._imagenes:
        box.grid_remove()
    yield
    ctk.CTkLabel(box, text=t('save_mode'), font=fonts.FUENTE_CHICA,
                 text_color=colors.TEXT_GRAY, anchor='w').grid(row=0, column=0, sticky='ew')
    yield
    if getattr(view, 'design_system', False):
        from app.ui.styles import OptionField
        selector = OptionField(box, values=[t('save_copies'), t('save_overwrite')],
                               variable=view._save_choice, font=fonts.FUENTE_BASE, width=220)
    else:
        selector = ctk.CTkOptionMenu(box, values=[t('save_copies'), t('save_overwrite')],
            variable=view._save_choice, font=fonts.FUENTE_BASE, width=220,
            fg_color=colors.DROPZONE_BG, button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER, text_color=colors.TEXT_COLOR,
            dropdown_fg_color=colors.PANEL_BG, dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER)
    selector.grid(row=0, column=1, sticky='e', padx=(12, 0), pady=(4, 4))
    yield


def set_visible(view, visible):
    """Muestra u oculta controles de salida según el módulo activo."""
    for group in getattr(view, '_save_groups', []):
        if visible and not group.winfo_manager():
            group.grid()
        elif not visible and group.winfo_manager():
            group.grid_remove()


def mode(view):
    """Devuelve la política de guardado actualmente seleccionada."""
    return 'overwrite' if view._save_choice.get() == t('save_overwrite') else 'copies'


def prepare(view, paths, target_format, proceed, *, resources=(), button=None, text=None, folder=None, notice=''):
    """Snapshot before IO; header reads stay off Tk and no model is loaded."""
    choice = mode(view)
    folder = (folder or filedialog.askdirectory(title=t('select_output_folder'), parent=view)) if choice == 'copies' else None
    if choice == 'copies' and not folder:
        return False
    paths, resources = tuple(paths), tuple(resources)
    def ready(plan):
        """Indica si la selección y el plan permiten guardar."""
        message = t('save_confirm').format(replace=plan.replacements, copies=plan.copies)
        if choice == 'overwrite' and any(not item.error and item.source_format != item.target_format for item in plan.items):
            message += '\n\n' + t('save_format_hint')
        if notice:
            message += '\n\n' + notice
        if not messagebox.askyesno(t('save_mode'), message, parent=view):
            return
        proceed(folder, plan)
    return view._submit_job(lambda: plan_outputs(paths, folder, choice, target_format, resources=resources),
                            on_success=ready, button=button, text=text)


def refresh(view, result):
    """Actualiza el resumen de rutas y conflictos del plan."""
    rows = result.get('resultados', []) if isinstance(result, dict) else []
    changed = [row['ruta_entrada'] for row in rows if row.get('estado') == 'saved' and row.get('reemplazado')]
    for path in changed:
        image_cache.invalidate(path)
    view._last_save_result = result
    if hasattr(view, '_virtual_file_list'):
        statuses = {}
        for row in rows:
            status = t({'saved': 'save_saved', 'unchanged': 'save_skipped', 'error': 'error_generic'}[row['estado']])
            if row.get('exif_no_aplicado'):
                status += ' · ' + t('save_exif_not_applied')
            if row['estado'] == 'error':
                status += ': ' + t(row['error'])
            if row['estado'] == 'saved' and row['tam_resultado'] > row['tam_original']:
                delta = row['tam_resultado'] - row['tam_original']
                status += f" · +{delta} B (+{round(delta / row['tam_original'] * 100, 1)}%)"
            statuses[row['ruta_entrada']] = status
        view._virtual_file_list.statuses = statuses
        view._virtual_file_list.sync(view._imagenes)
    if changed:
        if hasattr(view, '_preview_input_keys'):
            view._preview_input_keys.clear()
            view._last_preview_key = None
            if view._imagenes:
                view._cargar_preview_base(view._imagenes[0])


def summary(result, *, strip=False):
    """Genera un resumen legible de los destinos calculados."""
    rows = result.get('resultados', [])
    text = t('save_result').format(saved=result.get('ok', 0), skipped=result.get('sin_mejora', 0),
                                   errors=result.get('errores', 0))
    valid = [row for row in rows if row.get('estado') != 'error']
    before = sum(row.get('tam_original', 0) for row in valid)
    after = sum(row.get('tam_resultado', row.get('tam_comprimido', 0)) for row in valid)
    if before:
        from app.modules.compress import formatear_bytes
        text += f' · {formatear_bytes(before)} → {formatear_bytes(after)}'
        growth = [row for row in valid if row.get('estado') == 'saved' and row['tam_resultado'] > row['tam_original']]
        if growth:
            delta = sum(row['tam_resultado'] - row['tam_original'] for row in growth)
            base = sum(row['tam_original'] for row in growth)
            text += ' · ' + t('save_growth').format(count=len(growth), size=f'{delta} B', percent=round(delta/base*100, 1))
        else:
            text += ' · ' + t('save_reduction').format(percent=round((1-after/before)*100, 1))
    if strip and result.get('exif_no_aplicado'):
        text += ' · ' + t('save_exif_skipped').format(count=result['exif_no_aplicado'])
    if result.get('conflictos'):
        text += ' · ' + t('save_conflicts').format(count=result['conflictos'])
    return text
