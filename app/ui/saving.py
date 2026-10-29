"""Controles de guardado compartidos y confirmación asíncrona del destino."""
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.translations import t
from app.ui import colors, fonts
from app.ui.image_cache import image_cache
from app.utils.saving import plan_outputs
from app.ui.status import operation_summary


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


def prepare(view, paths, target_format, proceed, *, resources=(), button=None, text=None, folder=None, notice='',
            format_resolver=None, format_notice=''):
    """Snapshot before IO; header reads stay off Tk and no model is loaded."""
    choice = mode(view)
    folder = (folder or filedialog.askdirectory(title=t('select_output_folder'), parent=view)) if choice == 'copies' else None
    if choice == 'copies' and not folder:
        return False
    paths, resources = tuple(paths), tuple(resources)
    def ready(plan):
        """Indica si la selección y el plan permiten guardar."""
        message = t('save_confirm').format(replace=plan.replacements, copies=plan.copies)
        conversions = sum(not item.error and item.source_format != item.target_format for item in plan.items)
        if conversions and format_notice:
            message += '\n\n' + format_notice.format(count=conversions)
        elif choice == 'overwrite' and conversions:
            message += '\n\n' + t('save_format_hint')
        if notice:
            message += '\n\n' + notice
        if not messagebox.askyesno(t('save_mode'), message, parent=view):
            return
        proceed(folder, plan)
    return view._submit_job(lambda: plan_outputs(paths, folder, choice, target_format, resources=resources,
                                                format_resolver=format_resolver),
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
            status = t({'saved': 'save_saved', 'unchanged': 'save_skipped',
                        'skipped': 'save_omitted', 'error': 'error_generic'}[row['estado']])
            if row['estado'] == 'skipped':
                status += ': ' + t(row['motivo'])
            if row.get('exif_no_aplicado'):
                status += ' · ' + t('save_exif_not_applied')
            if row['estado'] == 'error':
                status += ': ' + t(row['error'])
            statuses[row['ruta_entrada']] = status
        view._virtual_file_list.statuses = statuses
        view._virtual_file_list.sync(view._imagenes)
    if changed:
        if hasattr(view, '_preview_input_keys'):
            view._preview_input_keys.clear()
            view._last_preview_key = None
            if view._imagenes:
                view._cargar_preview_base(view._imagenes[0])


def summary(result, *, strip=False, size_notice=False):
    """Resume el resultado; los datos completos permanecen en el objeto original."""
    text = operation_summary(result.get('ok', 0), result.get('errores', 0),
        unchanged=result.get('sin_mejora', 0), skipped=result.get('omitidos', 0))
    if size_notice and any(row.get('estado') == 'saved' and
            row.get('tam_resultado', 0) > row.get('tam_original', 0) for row in result.get('resultados', [])):
        text += ' · ' + t('status_size_increased')
    if strip and result.get('exif_no_aplicado'):
        text += ' · ' + t('status_exif_not_applied').format(count=result['exif_no_aplicado'])
    return text
