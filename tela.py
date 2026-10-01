"""Espelhamento explícito por USB com scrcpy oficial, sem gravação."""
import queue
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from janela_video import find_process_window, embed, resize

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
        self.window = ttk.Frame(parent)
        self.hwnd = None
        self.deadline = 0
        self.last_size = None
        self.stopping = False
        self.failure = None
        self.events = queue.Queue()
        self.process = None
        self.closed = False
        self.devices = []
        frame = ttk.Frame(self.window, padding=18, width=360)
        frame.pack(side='left', fill='y')
        self.preview = tk.Frame(self.window, bg='#080d16', width=500, height=560)
        self.preview.pack(side='right', fill='both', expand=True, padx=12, pady=12)
        ttk.Label(frame, text='Tela do Android por USB', font=('Segoe UI', 20, 'bold')).pack(anchor='w', pady=8)
        ttk.Label(frame, text='No celular desbloqueado, ative a depuração USB e autorize este computador.\nNão funciona como remoção de senha. A sessão não grava vídeo nem áudio.', wraplength=330).pack(anchor='w', pady=8)
        self.status = ttk.Label(frame, text='Verifique a conexão para começar.', wraplength=330)
        self.status.pack(anchor='w', pady=8)
        self.choice = ttk.Combobox(frame, state='readonly', width=35)
        self.choice.pack(fill='x', pady=8)
        self.consent = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text='O proprietário autorizou\nvisualizar a tela nesta sessão.', variable=self.consent).pack(anchor='w', pady=8)
        row = ttk.Frame(frame)
        row.pack(anchor='w', pady=10)
        self.check = ttk.Button(row, text='Verificar autorização USB', command=self.scan)
        self.check.pack(fill='x', pady=4)
        self.start = ttk.Button(row, text='Visualizar tela', command=self.mirror, state='disabled')
        self.start.pack(fill='x', pady=4)
        ttk.Button(row, text='Encerrar sessão', command=self.stop).pack(fill='x', pady=4)
        ttk.Label(frame, text='Somente visualização, sem controle pelo mouse.\nFechar o aplicativo encerra a sessão.', wraplength=330).pack(anchor='w', pady=8)
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
            self.hwnd = None
            self.last_size = None
            self.status.configure(text=self.failure or ('Sessão encerrada.' if code == 0 or self.stopping else 'Espelhamento não concluiu. Confira o cabo, a autorização e a compatibilidade do aparelho.'))
            self.stopping = False
            self.start.configure(state='normal' if self.devices else 'disabled')
        if self.process is not None and not self.stopping:
            try:
                if not self.hwnd:
                    handle = find_process_window(self.process.pid)
                    if handle:
                        embed(handle, self.preview.winfo_id())
                        self.hwnd = handle
                        self.status.configure(text='Tela conectada dentro do Conecta. Somente visualização.')
                    elif time.monotonic() > self.deadline:
                        raise TimeoutError('O vídeo não abriu em 25 segundos. Verifique o aparelho e tente novamente.')
                if self.hwnd:
                    size = (self.preview.winfo_width(), self.preview.winfo_height())
                    if size != self.last_size:
                        resize(self.hwnd, *size)
                        self.last_size = size
            except OSError as exc:
                self.failure = str(exc)
                self.stop()
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
            self.hwnd = None
            self.failure = None
            self.stopping = False
            self.last_size = None
            self.deadline = time.monotonic() + 25
            self.process = subprocess.Popen([str(TOOLS / 'scrcpy.exe'), '--serial', serial,
                '--no-control', '--no-audio', '--max-size=1280', '--window-borderless', '--window-width=400', '--window-height=600', '--window-title=Conecta - Video integrado'],
                cwd=str(TOOLS), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            self.start.configure(state='disabled')
            self.status.configure(text='Conectando vídeo ao painel do aplicativo…')
        except OSError as exc:
            self.status.configure(text=str(exc))

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.stopping = True
            self.process.terminate()

    def close(self):
        self.stop()
        self.closed = True
        self.window.destroy()
