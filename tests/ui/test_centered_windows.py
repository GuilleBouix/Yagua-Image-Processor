"""Auxiliary windows follow their owner rather than the primary monitor."""
from time import monotonic, sleep

import customtkinter as ctk
import pytest

from app.ui.windows import center_on_parent


@pytest.mark.parametrize('scale', [1, .75, .5])
def test_dialog_centers_on_moved_owner(ui_root, scale):
    old_scale = ctk.ScalingTracker.widget_scaling
    ctk.set_widget_scaling(scale)
    try:
        ui_root.deiconify()
        ui_root.update()
        ui_root.state('normal')
        # Keep the Windows test away from the user's desktop while proving the
        # helper does not incorrectly clamp the result to the primary monitor.
        ui_root.geometry('900x600+12000+200')
        ui_root.minsize(900, 600)
        deadline = monotonic() + 3
        while monotonic() < deadline:
            ui_root.update()
            if (ui_root.winfo_width(), ui_root.winfo_height()) == (900, 600):
                break
            sleep(.005)
        assert (ui_root.winfo_width(), ui_root.winfo_height()) == (900, 600)
        dialog = ctk.CTkToplevel(ui_root)
        dialog.geometry('540x320')
        dialog.transient(ui_root)
        ctk.CTkLabel(dialog, text='Save').pack()
        center_on_parent(dialog, ui_root, modal=True)
        deadline = monotonic() + 3
        while monotonic() < deadline and not dialog.winfo_ismapped():
            ui_root.update()
            sleep(.005)
        ui_root.update()
        assert dialog.winfo_ismapped()
        expected_x = ui_root.winfo_rootx() + (ui_root.winfo_width() - dialog.winfo_width()) // 2
        expected_y = ui_root.winfo_rooty() + (ui_root.winfo_height() - dialog.winfo_height()) // 2
        # Tk geometry places the outer frame; its client origin includes the
        # platform's title bar/border, whose size varies with the desktop theme.
        assert abs(dialog.winfo_x() - expected_x) <= 2, (
            ui_root.geometry(), ui_root.winfo_rootx(), ui_root.winfo_width(),
            dialog.geometry(), dialog.winfo_width(), expected_x)
        assert abs(dialog.winfo_y() - expected_y) <= 2
        assert ui_root.grab_current() is dialog
        dialog.destroy()
    finally:
        ctk.set_widget_scaling(old_scale)


def test_destroy_before_centering_cancels_callback(ui_root):
    dialog = ctk.CTkToplevel(ui_root)
    center_on_parent(dialog, ui_root, modal=True)
    dialog.destroy()
    ui_root.update()
    assert ui_root.grab_current() is None
