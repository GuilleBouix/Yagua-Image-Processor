"""Apply settings through the packaged Linux UI and verify real AppImage restarts.

Run on an X11 desktop or under Xvfb. All preferences and logs live in the new
report directory; no installed user profile or application code is modified.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import tkinter as tk
import traceback


TEXT = {
    'English': ('Choose a tool to get started.', 'Settings', 'Apply', 'Enter now'),
    'Español': ('Elegí una herramienta para empezar.', 'Ajustes', 'Aplicar', 'Entrar ahora'),
}
TREE = '''
proc qa_restart_tree {w} {
    set rows {}
    foreach child [winfo children $w] {
        set text ""
        catch {set text [$child cget -text]}
        lappend rows [list $child [winfo class $child] $text [winfo ismapped $child]]
        foreach row [qa_restart_tree $child] {lappend rows $row}
    }
    return $rows
}
'''


def process_exited(pid):
    """Detecta procesos terminados que aún figuran como zombis en Linux."""
    try:
        state = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
        return state == 'Z'
    except FileNotFoundError:
        return True


class RestartProbe:
    """Controla sólo las instancias nuevas de Tk mediante eventos nativos."""

    def __init__(self, client, timeout, profile_home=None):
        """Inicializa el control y registra los intérpretes ya presentes."""
        self.client = client
        self.timeout = timeout
        self.before = set(self.peers())
        self.peer = None
        self.profile_home = profile_home

    def renew_client(self):
        """Renueva el cliente Tk antes de contactar al proceso reiniciado.

        Algunas versiones de Tk conservan el XID anterior bajo el mismo nombre.
        Consultarlo mientras el proceso termina puede bloquear el envío síncrono.
        """
        self.client.destroy()
        self.client = tk.Tk()
        self.client.withdraw()
        self.client.tk.call('tk', 'appname', f'yagua-restart-probe-{os.getpid()}')

    def owned_peers(self):
        """Identifica las instancias propias usando el perfil temporal de CI."""
        if self.profile_home is None:
            return set(self.peers()) - self.before
        owned = set()
        marker = b'HOME=' + os.fsencode(self.profile_home) + b'\0'
        own_name = self.client.tk.call('tk', 'appname')
        for peer in self.peers():
            if peer == own_name:
                continue
            try:
                pid = int(self.client.tk.call('send', peer, 'pid'))
                if marker in Path(f'/proc/{pid}/environ').read_bytes():
                    owned.add(peer)
            except (tk.TclError, FileNotFoundError, PermissionError, ProcessLookupError):
                pass
        return owned

    def peers(self):
        """Devuelve los intérpretes Tk visibles en la pantalla actual."""
        return self.client.tk.splitlist(self.client.tk.call('winfo', 'interps'))

    def remote(self, script):
        """Ejecuta un script Tcl en la instancia de Yagua controlada."""
        return self.client.tk.call('send', self.peer, script)

    def call(self, *args):
        """Cita argumentos como Tcl y los envía a la instancia remota."""
        quote = getattr(tk, '_join')
        return self.remote(quote(tuple(str(arg) for arg in args)))

    def wait(self, check, message):
        """Reintenta una condición hasta cumplirla o agotar el tiempo límite."""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            self.client.update()
            try:
                value = check()
                if value:
                    return value
            except tk.TclError:
                pass  # The previous interpreter can disappear during restart.
            time.sleep(.05)
        raise TimeoutError(message)

    def tree(self):
        """Obtiene los widgets visibles de la ventana remota."""
        return [self.client.tk.splitlist(row)
                for row in self.client.tk.splitlist(self.remote('qa_restart_tree .'))]

    def find(self, text):
        """Busca un control visible cuyo texto coincide exactamente."""
        return next((w for w, _, label, mapped in self.tree()
                     if int(mapped) and label.strip() == text), None)

    def home(self, language, previous_pid=None):
        """Espera un proceso nuevo, la pantalla Inicio y el fin de la carga."""
        def ready():
            """Comprueba que la nueva instancia muestre Inicio en el idioma pedido."""
            peers = self.owned_peers()
            for peer in peers:
                self.peer = peer
                try:
                    pid = int(self.remote('pid'))
                    if pid == previous_pid:
                        continue
                    self.remote(TREE)
                    if self.find(TEXT[language][0]) and not self.find(TEXT[language][3]):
                        return pid
                except tk.TclError:
                    continue
            return None
        return self.wait(ready, f'AppImage did not reopen Home in {language}')

    def click(self, text):
        """Envía un clic a un control visible identificado por su etiqueta."""
        widget = self.wait(lambda: self.find(text), f'Missing visible control: {text}')
        event = getattr(tk, '_join')(
            ('event', 'generate', widget, '<Button-1>', '-x', '5', '-y', '5'))
        self.call('after', 0, event)

    def choose(self, value):
        """Elige una opción real del menú CTk sin reemplazar su callback."""
        for widget, kind, _, _ in self.tree():
            if kind != 'Menu':
                continue
            end = self.call(widget, 'index', 'end')
            if end == 'none':
                continue
            for index in range(int(end) + 1):
                if (self.call(widget, 'type', index) != 'separator'
                        and self.call(widget, 'entrycget', index, '-label').strip() == value):
                    self.call(widget, 'invoke', index)
                    return
        raise AssertionError(f'Dropdown option not found: {value}')

    def open_settings(self, language):
        """Abre Ajustes y devuelve la altura del botón Aplicar."""
        self.click(TEXT[language][1])
        apply = self.wait(lambda: self.find(TEXT[language][2]), 'Settings did not open')
        button = self.call('winfo', 'parent', apply)
        return int(self.call('winfo', 'height', button))

    def close(self):
        """Cierra sólo las instancias de Yagua creadas por esta sonda."""
        for peer in self.owned_peers():
            try:
                self.client.tk.call('send', peer, 'destroy .')
            except tk.TclError:
                pass


def run(executable: Path, directory: Path, timeout=180) -> dict:
    """Comprueba que Aplicar guarde ajustes y reinicie el paquete correctamente."""
    directory.mkdir(parents=True, exist_ok=False)
    home = directory / 'home'
    settings = home / '.config/Yagua/user_settings.json'
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({'language': 'English', 'theme': 'Default', 'ui_scale': 100}))
    env = os.environ.copy()
    env.update(HOME=str(home.resolve()), OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    for key in ('YAGUA_PACKAGE_SELFTEST', 'YAGUA_PACKAGE_SELFTEST_MODE'):
        env.pop(key, None)
    report = {'status': 'failed', 'executable': str(executable.resolve()), 'restarts': []}
    client = tk.Tk()
    client.withdraw()
    client.tk.call('tk', 'appname', f'yagua-restart-probe-{os.getpid()}')
    probe = RestartProbe(client, timeout, home.resolve())
    process = None
    try:
        with (directory / 'process.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen([str(executable.resolve())], cwd=directory,
                                       env=env, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            pid = probe.home('English')
            print(f'PASS initial startup: pid={pid}', flush=True)
            language = 'English'
            base_height = probe.open_settings(language)
            for next_language, theme, scale in (
                ('Español', 'Tokyo Night', 75), ('English', 'Default', 50),
                ('English', 'Default', 100),
            ):
                probe.choose(next_language)
                probe.choose(theme)
                probe.click(f'{scale}%')
                print(f'APPLY {next_language}, {theme}, {scale}%', flush=True)
                probe.click(TEXT[language][2])
                print('WAIT replacement UI', flush=True)
                started = time.monotonic()
                probe.wait(lambda: process_exited(pid), 'Previous AppImage did not exit')
                probe.renew_client()
                new_pid = probe.home(next_language, previous_pid=pid)
                saved = json.loads(settings.read_text(encoding='utf-8'))
                assert (saved['language'], saved['theme'], saved['ui_scale']) == (
                    next_language, theme, scale), saved
                height = probe.open_settings(next_language)
                assert probe.find(theme) and probe.find(next_language)
                assert abs(height - base_height * scale / 100) <= 3, (height, base_height, scale)
                report['restarts'].append({
                    'old_pid': pid, 'new_pid': new_pid, 'language': next_language,
                    'theme': theme, 'scale': scale, 'apply_height': height,
                    'seconds': time.monotonic() - started,
                })
                print(f'PASS real restart: {next_language}, {theme}, {scale}%', flush=True)
                pid, language = new_pid, next_language
            report['status'] = 'passed'
    except Exception:
        report['error'] = traceback.format_exc()
        try:
            report['widgets'] = probe.tree()
        except tk.TclError:
            pass
    finally:
        probe.close()
        if process is not None:
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=15)
        probe.client.destroy()
        (directory / 'restart.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if report['status'] != 'passed':
        raise RuntimeError(f'Restart verification failed: {directory / "restart.json"}\n'
                           + report.get('error', ''))
    return report


def main():
    """Lee los argumentos de CI y ejecuta la verificación del reinicio real."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--timeout', type=float, default=180)
    args = parser.parse_args()
    run(args.executable, args.directory.resolve(), args.timeout)


if __name__ == '__main__':
    main()
