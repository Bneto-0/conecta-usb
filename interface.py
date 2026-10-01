"""Interface escura com navegação lateral e painel integrado de vídeo."""
import tkinter as tk
from tkinter import ttk, messagebox
from atendimento import Atendimento

BG = '#171b20'
PANEL = '#22282f'
TEXT = '#eef2f6'
MUTED = '#95a3b2'
ACCENT = '#47c6dc'

def label(parent, text, size=10, color=TEXT, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=color,
                    font=('Segoe UI', size), anchor='w', justify='left', **kwargs)

def button(parent, text, command, primary=False):
    return tk.Button(parent, text=text, command=command, bg=ACCENT if primary else '#303941',
        fg='#102029' if primary else TEXT, activebackground='#398d9e', activeforeground='white',
        disabledforeground='#74818a', relief='flat', bd=0, padx=15, pady=10,
        cursor='hand2', font=('Segoe UI', 10))

def build(app, root):
    root.title('Conecta USB • v0.2.0')
    root.geometry('1150x760')
    root.minsize(1040, 680)
    root.configure(bg=BG)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('.', background=BG, foreground=TEXT, font=('Segoe UI', 10))
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG, foreground=TEXT)
    style.configure('TCheckbutton', background=BG, foreground=TEXT)
    style.map('TCheckbutton', background=[('active', PANEL)])
    style.configure('TButton', background='#303941', foreground=TEXT, padding=9)
    style.map('TButton', background=[('active', '#36525b')], foreground=[('disabled', '#74818a')])
    style.configure('TEntry', fieldbackground=PANEL, foreground=TEXT, insertcolor=TEXT)
    style.configure('TCombobox', fieldbackground=PANEL, foreground=TEXT, arrowcolor=TEXT)
    style.map('TCombobox', fieldbackground=[('readonly', PANEL)], foreground=[('readonly', TEXT)])
    style.configure('Treeview', rowheight=32, background=PANEL, fieldbackground=PANEL, foreground=TEXT, borderwidth=0)
    style.configure('Treeview.Heading', background='#2b333b', foreground=MUTED, padding=8)
    style.map('Treeview', background=[('selected', '#294653')], foreground=[('selected', '#ffffff')])
    style.configure('Horizontal.TProgressbar', background=ACCENT, troughcolor='#101419', borderwidth=0)

    side = tk.Frame(root, bg='#12161b', width=206)
    side.pack(side='left', fill='y')
    side.pack_propagate(False)
    label(side, 'CONECTA', 23, ACCENT).pack(anchor='w', padx=22, pady=(30, 0))
    label(side, 'ASSISTÊNCIA DE DISPOSITIVOS', 8, MUTED).pack(anchor='w', padx=22, pady=(4, 30))
    app.nav = {}
    for key, text, command in [
        ('home', '⌂   Visão geral', lambda: show(app, 'home')),
        ('android', '▣   Celular Android', app.open_screen),
        ('service', '+   Novo atendimento', lambda: Atendimento(root)),
        ('windows', '▤   PC / Windows', lambda: new_windows(root)),
    ]:
        item = button(side, text, command)
        item.configure(anchor='w', bg='#12161b')
        item.pack(fill='x', padx=10, pady=3)
        app.nav[key] = item
    tk.Frame(side, bg='#303941', height=1).pack(fill='x', padx=20, pady=20)
    button(side, 'Sobre o aplicativo', lambda: messagebox.showinfo('Conecta USB 0.2.0',
        'Diagnóstico, atendimento e visualização Android autorizada.\n\nSem gravação, formatação ou remoção de senhas.\nA tela Android requer autorização ADB no aparelho.', parent=root)).pack(fill='x', padx=10)
    label(side, '●  PROCESSAMENTO LOCAL\nv0.2.0 · Windows', 9, MUTED).pack(side='bottom', padx=20, pady=24)

    outer = tk.Frame(root, bg=BG)
    outer.pack(side='left', fill='both', expand=True)
    header = tk.Frame(outer, bg=BG, padx=26, pady=20)
    header.pack(fill='x')
    app.page_title = label(header, 'Central de atendimento', 20)
    app.page_title.pack(side='left')
    label(header, 'USB  /  ACESSO AUTORIZADO', 9, ACCENT).pack(side='right')
    app.content = tk.Frame(outer, bg=BG)
    app.content.pack(fill='both', expand=True)
    app.home = tk.Frame(app.content, bg=BG, padx=26)
    app.home.pack(fill='both', expand=True)
    main = app.home
    label(main, '01  Conectar aparelho     /     02  Verificar acesso     /     03  Iniciar atendimento', 10, MUTED).pack(fill='x', pady=(0, 20))
    card = tk.Frame(main, bg=PANEL, padx=22, pady=18)
    card.pack(fill='x')
    phone = tk.Canvas(card, width=88, height=140, bg=PANEL, highlightthickness=0)
    phone.pack(side='left', padx=(0, 24))
    phone.create_rectangle(10, 3, 77, 136, outline='#697984', width=2)
    phone.create_rectangle(16, 16, 71, 119, fill='#17323e', outline='')
    phone.create_text(44, 63, text='USB', fill=ACCENT, font=('Segoe UI', 14, 'bold'))
    phone.create_text(44, 85, text='CONECTA', fill='#9cb4bf', font=('Segoe UI', 7))
    phone.create_line(34, 9, 53, 9, fill='#697984', width=2)
    info = tk.Frame(card, bg=PANEL)
    info.pack(side='left', fill='both', expand=True)
    label(info, 'DISPOSITIVO CONECTADO', 9, MUTED).pack(anchor='w')
    app.device_name = label(info, 'Verificando conexão…', 20)
    app.device_name.pack(anchor='w', pady=(5, 4))
    label(info, 'Diagnóstico USB e tela Android no mesmo lugar.', 10, MUTED).pack(anchor='w', pady=(0, 12))
    actions = tk.Frame(info, bg=PANEL)
    actions.pack(anchor='w')
    button(actions, 'Abrir tela do Android', app.open_screen, True).pack(side='left', padx=(0, 8))
    button(actions, 'Novo atendimento', lambda: Atendimento(root)).pack(side='left')
    bar = tk.Frame(main, bg=BG)
    bar.pack(fill='x', pady=18)
    label(bar, 'CONEXÕES DO WINDOWS', 10, MUTED).pack(side='left')
    app.export_button = button(bar, 'Salvar relatório', app.export)
    app.export_button.configure(state='disabled')
    app.export_button.pack(side='right', padx=(8, 0))
    app.scan_button = button(bar, 'Verificar USB', app.start_scan)
    app.scan_button.pack(side='right')
    app.table = ttk.Treeview(main, columns=('name','class','status'), show='headings', height=4)
    for key, title, width in [('name','Dispositivo',350),('class','Interface',140),('status','Status',110)]:
        app.table.heading(key,text=title)
        app.table.column(key,width=width,minwidth=90)
    app.table.pack(fill='both',expand=True)
    app.table.bind('<<TreeviewSelect>>',app.select)
    app.detail = label(main, 'Selecione uma interface para ver o diagnóstico.', 10, MUTED, wraplength=730)
    app.detail.pack(fill='x',pady=14)
    footer=tk.Frame(outer,bg='#12161b',padx=24,pady=12)
    footer.pack(fill='x')
    app.progress=ttk.Progressbar(footer,mode='indeterminate',length=95)
    app.progress.pack(side='right',padx=8)
    app.status=label(footer,'Pronto para verificar.',9,MUTED)
    app.status.pack(side='left')
    show(app,'home')

def new_windows(root):
    form=Atendimento(root)
    form.vars['sistema'].set('Windows')
    form.system_changed()

def show(app, page):
    app.home.pack_forget()
    for screen in app.screen_windows:
        screen.window.pack_forget()
    if page=='home':
        app.home.pack(fill='both',expand=True)
        app.page_title.configure(text='Central de atendimento')
    else:
        app.screen_windows[0].window.pack(fill='both',expand=True)
        app.page_title.configure(text='Celular Android • tela ao vivo')
    for key, item in app.nav.items():
        item.configure(bg='#233d49' if key==page else '#12161b',fg=ACCENT if key==page else TEXT)
