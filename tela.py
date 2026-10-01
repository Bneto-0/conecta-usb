"""Espelhamento explícito por USB com scrcpy oficial, sem gravação."""
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

TOOLS = Path(__file__).parent / 'tools' / 'scrcpy-win64-v4.1'

def adb_devices():
    result = subprocess.run([str(TOOLS / 'adb.exe'), 'devices', '-l'], capture_output=True,
        encoding='utf-8', errors='replace', timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'Falha ao consultar ADB')
    devices = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] in ('device', 'unauthorized', 'offline', 'recovery', 'sideload'):
            # Apenas transporte USB, não sessões ADB pela rede.
            if ':' not in parts[0] and not parts[0].startswith('emulator-'):
                devices.append((parts[0], parts[1]))
    return devices

class Tela:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title('Conecta • Tela do Android')
        self.window.geometry('720x440')
        self.events = queue.Queue()
        self.process = None
        self.closed = False
        self.devices = []
        frame = ttk.Frame(self.window, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Tela do Android por USB', font=('Segoe UI', 20, 'bold')).pack(anchor='w', pady=8)
        ttk.Label(frame, text='No celular desbloqueado, ative a depuração USB e autorize este computador.\nNão funciona como remoção de senha. A sessão não grava vídeo nem áudio.', wraplength=650).pack(anchor='w', pady=8)
        self.status = ttk.Label(frame, text='Verifique a conexão para começar.', wraplength=650)
        self.status.pack(anchor='w', pady=8)
        self.choice = ttk.Combobox(frame, state='readonly', width=65)
        self.choice.pack(fill='x', pady=8)
        self.consent = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text='O proprietário autorizou visualizar a tela nesta sessão.', variable=self.consent).pack(anchor='w', pady=8)
        row = ttk.Frame(frame)
        row.pack(anchor='w', pady=10)
        self.check = ttk.Button(row, text='Verificar autorização USB', command=self.scan)
        self.check.pack(side='left')
        self.start = ttk.Button(row, text='Visualizar tela', command=self.mirror, state='disabled')
        self.start.pack(side='left', padx=8)
        ttk.Button(row, text='Encerrar sessão', command=self.stop).pack(side='left')
        ttk.Label(frame, text='Visualização somente: teclado e mouse não controlam o celular.\nFechar esta janela encerra o espelhamento.', wraplength=650).pack(anchor='w', pady=8)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.after(100, self.poll)

    def scan(self):
        self.check.configure(state='disabled')
        self.start.configure(state='disabled')
        self.devices = []
        self.choice.set('')
        self.choice.configure(values=[])
        self.status.configure(text='Consultando autorização do Android…')
        def worker():
            try:
                self.events.put(('devices', adb_devices()))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        if self.closed:
            return
        try:
            kind, value = self.events.get_nowait()
            self.check.configure(state='normal')
            if kind == 'devices':
                self.devices = value
                self.choice.configure(values=[f'{i + 1}. {serial[-4:]} • {state}' for i, (serial, state) in enumerate(value)])
                if value:
                    self.choice.current(0)
                self.start.configure(state='normal' if value and self.process is None else 'disabled')
                self.status.configure(text='Selecione o aparelho. "device" = autorizado; "unauthorized" = aceite a solicitação na tela do celular.' if value else 'Nenhuma conexão ADB por USB encontrada. Verifique depuração USB, cabo e autorização na tela do celular.')
            elif kind == 'error':
                self.status.configure(text=value)
        except queue.Empty:
            pass
        if self.process is not None and self.process.poll() is not None:
            code = self.process.returncode
            self.process = None
            self.status.configure(text='Sessão encerrada.' if code == 0 else 'Espelhamento não concluiu. Confira o cabo, a autorização e a compatibilidade do aparelho.')
            self.start.configure(state='normal' if self.devices else 'disabled')
        self.window.after(150, self.poll)

    def mirror(self):
        index = self.choice.current()
        if self.process is not None or index < 0:
            return
        if not self.consent.get():
            messagebox.showinfo('Autorização da sessão', 'Confirme a autorização do proprietário para visualizar a tela.', parent=self.window)
            return
        serial, state = self.devices[index]
        if state != 'device':
            self.status.configure(text='Aparelho não autorizado ou indisponível. Autorize no celular e verifique novamente.')
            return
        try:
            self.process = subprocess.Popen([str(TOOLS / 'scrcpy.exe'), '--serial', serial,
                '--no-control', '--no-audio', '--max-size=1280', '--window-title=Conecta - Tela autorizada'],
                cwd=str(TOOLS), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            self.start.configure(state='disabled')
            self.status.configure(text='Abrindo visualização em uma janela separada…')
        except OSError as exc:
            self.status.configure(text=str(exc))

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()

    def close(self):
        self.stop()
        self.closed = True
        self.window.destroy()
