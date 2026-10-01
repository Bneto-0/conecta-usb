"""Diagnóstico USB local: somente leitura dos dispositivos do Windows."""
import json
import queue
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from atendimento import Atendimento
from tela import Tela
from interface import build, show

QUERY = r"""$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$items = @(Get-PnpDevice -PresentOnly | Where-Object {
 $_.Class -eq 'WPD' -or $_.FriendlyName -match 'Motorola|Moto|Samsung|Android|ADB|MTP|iPhone|Unknown USB|USB desconhecido|Dispositivo desconhecido' -or
 $_.InstanceId -match '^USB\\VID_(22B8|04E8|18D1|05AC)'
} | Select-Object Status,Class,FriendlyName,InstanceId)
ConvertTo-Json -InputObject $items -Compress
"""

def scan_devices():
    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', QUERY],
        capture_output=True, encoding='utf-8', errors='replace', timeout=40,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'O Windows não concluiu a consulta.')
    devices = json.loads(result.stdout.strip() or '[]')
    return devices if isinstance(devices, list) else [devices]

class App:
    def __init__(self, root):
        self.root = root
        self.devices = []
        self.checked_at = None
        self.events = queue.Queue()
        self.screen_windows = []
        build(self, root)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)
        root.after(300, self.start_scan)

    def open_screen(self):
        if not self.screen_windows:
            screen = Tela(self.content)
            self.screen_windows.append(screen)
        show(self, 'android')

    def close(self):
        for screen in self.screen_windows:
            if not screen.closed:
                screen.close()
        self.root.destroy()

    def start_scan(self):
        self.progress.start(12)
        self.scan_button.configure(state='disabled')
        self.export_button.configure(state='disabled')
        self.status.configure(text='Consultando os dispositivos presentes no Windows…')
        def worker():
            try:
                self.events.put(('success', scan_devices()))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            kind, value = self.events.get_nowait()
            self.progress.stop()
            self.scan_button.configure(state='normal')
            self.table.delete(*self.table.get_children())
            self.devices = []
            self.checked_at = None
            if kind == 'error':
                self.status.configure(text='Não foi possível concluir a verificação.')
                self.detail.configure(text='Falha na consulta. Tente novamente. Nenhum dado foi alterado.')
                messagebox.showerror('Falha na consulta', value)
            else:
                self.devices = value
                names = [d.get('FriendlyName') for d in value if d.get('Class') == 'WPD']
                self.device_name.configure(text=', '.join(names) if names else 'Nenhum celular identificado')
                self.checked_at = datetime.now().isoformat(timespec='seconds')
                self.export_button.configure(state='normal')
                for index, device in enumerate(value):
                    self.table.insert('', 'end', iid=str(index), values=(device.get('FriendlyName') or 'Sem nome', device.get('Class'), device.get('Status')))
                self.status.configure(text=f'{len(value)} interface(s) encontrada(s) • {self.checked_at.replace("T", " ")}')
                self.detail.configure(text='Nenhum celular identificado. Teste um cabo de dados e outra porta USB. A ausência nesta lista não comprova defeito no aparelho.')
                if value:
                    self.table.selection_set('0')
                    self.select()
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def select(self, event=None):
        selection = self.table.selection()
        if not selection:
            return
        device = self.devices[int(selection[0])]
        message = 'O Windows reconheceu esta interface USB. Isso não confirma que o celular está desbloqueado ou que seus arquivos estão acessíveis.'
        if device.get('Status') != 'OK':
            message = 'O Windows informa um problema nesta interface. Confira o cabo, a porta e o driver no Gerenciador de Dispositivos.'
        self.detail.configure(text=message + '\n\nEsta versão apenas identifica a conexão; não remove senha ou padrão.')

    def export(self):
        target = filedialog.asksaveasfilename(title='Salvar relatório local', defaultextension='.json',
            initialfile='diagnostico-usb.json', filetypes=[('Relatório JSON', '*.json')])
        if not target:
            return
        # O identificador USB completo pode conter o número de série: não exportá-lo.
        report = {'verificado_em': self.checked_at, 'modo': 'somente leitura',
                  'dispositivos': [{k: d.get(k) for k in ('FriendlyName', 'Class', 'Status')} for d in self.devices]}
        try:
            Path(target).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            messagebox.showinfo('Relatório salvo', 'Relatório salvo no local escolhido, sem o número de série do aparelho.')
        except OSError as exc:
            messagebox.showerror('Não foi possível salvar', str(exc))

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
