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
        root.title('Conecta • Diagnóstico USB')
        root.geometry('1020x680')
        root.minsize(760, 560)
        root.configure(bg='#101827')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', rowheight=34, font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        main = tk.Frame(root, bg='#101827', padx=28, pady=24)
        main.pack(fill='both', expand=True)
        def label(text, size=11, color='#becbdd'):
            widget = tk.Label(main, text=text, bg='#101827', fg=color,
                              font=('Segoe UI', size), anchor='w', justify='left')
            widget.pack(fill='x', pady=(0, 12))
            return widget
        label('CONECTA  /  DIAGNÓSTICO LOCAL', 11, '#61dcc0')
        label('Seu aparelho, conectado.', 26, '#ffffff')
        label('Verifique a conexão USB sem alterar os dados do celular.')
        label('Diagnóstico, atendimento e visualização autorizada • Sem formatação.', 10, '#61dcc0')
        bar = tk.Frame(main, bg='#101827')
        bar.pack(fill='x', pady=(4, 18))
        self.scan_button = tk.Button(bar, text='Verificar conexão USB', command=self.start_scan,
            bg='#61dcc0', fg='#101827', relief='flat', padx=18, pady=10,
            font=('Segoe UI', 11, 'bold'))
        self.scan_button.pack(side='left')
        self.export_button = tk.Button(bar, text='Salvar relatório', command=self.export,
            state='disabled', padx=16, pady=10, relief='flat', font=('Segoe UI', 10))
        self.export_button.pack(side='left', padx=12)
        tk.Button(bar, text='Novo atendimento', command=lambda: Atendimento(root),
                  padx=16, pady=10, relief='flat', font=('Segoe UI', 10)).pack(side='left')
        self.screen_windows = []
        tk.Button(bar, text='Tela do Android', command=self.open_screen,
                  padx=16, pady=10, relief='flat', font=('Segoe UI', 10)).pack(side='left', padx=8)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.status = label('Pronto para verificar.', 11, '#ffffff')
        self.table = ttk.Treeview(main, columns=('name', 'class', 'status'), show='headings', height=6)
        for key, title, width in [('name', 'Dispositivo', 400), ('class', 'Interface', 150), ('status', 'Status Windows', 150)]:
            self.table.heading(key, text=title)
            self.table.column(key, width=width)
        self.table.pack(fill='both', expand=True)
        self.table.bind('<<TreeviewSelect>>', self.select)
        self.detail = tk.Label(main, text='Selecione um dispositivo para ver a orientação.',
            bg='#1c293b', fg='#e2eaf4', font=('Segoe UI', 11), justify='left',
            anchor='nw', padx=16, pady=16, wraplength=790)
        self.detail.pack(fill='x', pady=(18, 0))
        root.after(100, self.poll)
        root.after(300, self.start_scan)

    def open_screen(self):
        self.screen_windows.append(Tela(self.root))

    def close(self):
        for screen in self.screen_windows:
            if not screen.closed:
                screen.close()
        self.root.destroy()

    def start_scan(self):
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
