import json
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

LINKS = {
    'Android': 'https://support.google.com/android/answer/7663172?hl=pt-BR',
    'iPhone': 'https://support.apple.com/en-la/105090',
    'Windows': 'https://support.microsoft.com/en-gb/windows/security/identity-signin/troubleshoot-problems-signing-in-to-windows',
}
BLOCKS = {
    'Android': ('Padrão / PIN / senha da tela', 'Conta Google após restauração', 'Outro / não identificado'),
    'iPhone': ('Código da tela', 'Bloqueio de Ativação', 'Outro / não identificado'),
    'Windows': ('Senha da conta Microsoft', 'Senha de conta local', 'PIN do Windows', 'BitLocker', 'Senha ao ligar / BIOS', 'Outro / não identificado'),
}

def orientation(data):
    steps = []
    if not data['autorizacao']:
        steps.append('PENDENTE: confirmar a autorização do proprietário antes de qualquer serviço.')
    if data['dados'] == 'Não decidido':
        steps.append('PENDENTE: esclarecer se os dados precisam ser preservados. Não executar apagamento.')
    elif data['dados'] == 'Preservar todos os dados':
        steps.append('PRESERVAR: não restaurar nem reinstalar. Verificar recuperação de conta e backups existentes; não há garantia de acesso aos arquivos protegidos.')
    else:
        steps.append('O cliente declarou aceitar a perda dos dados locais. Este registro não executa nem autoriza automaticamente um procedimento específico; revisar o método e obter confirmação antes de apagar.')
    if data['conta'] != 'Acesso confirmado':
        steps.append('Confirmar o acesso à conta vinculada ou iniciar sua recuperação oficial com o cliente. Não registrar senhas neste formulário.')
    if data['sistema'] == 'Windows':
        if data['bloqueio'] == 'BitLocker':
            steps.append('Identificar a chave de recuperação do BitLocker com o proprietário ou a organização. Uma redefinição de senha não substitui essa chave.')
        elif data['bloqueio'] == 'Senha ao ligar / BIOS':
            steps.append('Encaminhar ao suporte do fabricante com modelo e comprovação de propriedade. Não confundir esse bloqueio com a senha do Windows.')
        else:
            steps.append('Consultar o guia Microsoft e identificar se o bloqueio é PIN, conta Microsoft ou conta local antes de selecionar o procedimento.')
    else:
        steps.append('Consultar o guia oficial e o procedimento específico do modelo. Uma restauração pode exigir a conta anteriormente vinculada e apagar os dados locais.')
    if data['backup'] != 'Backup confirmado':
        steps.append('Backup ainda não confirmado: não prometer recuperação de fotos e arquivos após apagar o aparelho.')
    steps.append('Esta versão registra e orienta o atendimento. Não remove senhas e não executa restaurações.')
    return '\n\n'.join(steps)

class Atendimento:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title('Conecta • Novo atendimento')
        self.window.geometry('860x780')
        self.window.minsize(760, 700)
        self.vars = {}
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text='Atendimento • senha esquecida', font=('Segoe UI', 20, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
        ttk.Label(frame, text='Use um nome ou código do cliente. Não registre senhas, PINs ou chaves de recuperação.').grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 14))
        fields = [
            ('cliente', 'Cliente / código', None),
            ('modelo', 'Marca e modelo', None),
            ('sistema', 'Sistema', tuple(BLOCKS)),
            ('bloqueio', 'Tipo de bloqueio', BLOCKS['Android']),
            ('conta', 'Conta vinculada', ('Não verificado', 'Acesso confirmado', 'Sem acesso', 'Não se aplica')),
            ('dados', 'Preferência sobre os dados', ('Não decidido', 'Preservar todos os dados', 'Aceita apagar todos os dados locais')),
            ('backup', 'Backup', ('Não verificado', 'Backup confirmado', 'Sem backup conhecido')),
        ]
        self.inputs = {}
        for row, (key, title, options) in enumerate(fields, start=2):
            ttk.Label(frame, text=title).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=6)
            var = self.vars[key] = tk.StringVar(value=options[0] if options else '')
            widget = ttk.Combobox(frame, textvariable=var, values=options, state='readonly') if options else ttk.Entry(frame, textvariable=var)
            widget.grid(row=row, column=1, sticky='ew', pady=6)
            self.inputs[key] = widget
            var.trace_add('write', self.changed)
        self.vars['bloqueio'].set('Outro / não identificado')
        self.inputs['sistema'].bind('<<ComboboxSelected>>', self.system_changed)
        self.authorized = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text='Registrei a autorização do proprietário para diagnóstico e orientação.', variable=self.authorized, command=self.changed).grid(row=9, column=0, columnspan=2, sticky='w', pady=10)
        buttons = ttk.Frame(frame)
        buttons.grid(row=10, column=0, columnspan=2, sticky='w', pady=8)
        ttk.Button(buttons, text='Gerar orientação', command=self.generate).pack(side='left')
        ttk.Button(buttons, text='Salvar atendimento…', command=self.save).pack(side='left', padx=8)
        ttk.Button(buttons, text='Abrir guia oficial', command=self.open_guide).pack(side='left')
        self.output = tk.Text(frame, wrap='word', height=12, font=('Segoe UI', 10), padx=12, pady=12)
        self.output.grid(row=11, column=0, columnspan=2, sticky='nsew')
        frame.rowconfigure(11, weight=1)
        self.show('Preencha o cadastro e clique em Gerar orientação. Nenhuma ação será executada no aparelho.')

    def show(self, text):
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', text)
        self.output.configure(state='disabled')

    def changed(self, *args):
        if hasattr(self, 'output'):
            self.show('Cadastro alterado. Clique em Gerar orientação para atualizar os próximos passos.')

    def system_changed(self, event=None):
        self.inputs['bloqueio'].configure(values=BLOCKS[self.vars['sistema'].get()])
        self.vars['bloqueio'].set('Outro / não identificado')

    def data(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        data['autorizacao'] = self.authorized.get()
        if not data['cliente'] or not data['modelo']:
            messagebox.showwarning('Dados necessários', 'Informe cliente/código e marca/modelo.', parent=self.window)
            return None
        return data

    def generate(self):
        data = self.data()
        if data:
            self.show(orientation(data))

    def open_guide(self):
        webbrowser.open(LINKS[self.vars['sistema'].get()])

    def save(self):
        data = self.data()
        if not data:
            return
        data.update(criado_em=datetime.now().isoformat(timespec='seconds'), orientacao=orientation(data), guia_oficial=LINKS[data['sistema']], versao=1)
        path = filedialog.asksaveasfilename(parent=self.window, title='Salvar atendimento', initialfile='atendimento-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.json', defaultextension='.json', filetypes=[('Atendimento JSON', '*.json')])
        if path:
            try:
                Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
                self.show(data['orientacao'])
                messagebox.showinfo('Salvo', 'Atendimento salvo no local escolhido. Nenhuma alteração foi feita no aparelho.', parent=self.window)
            except OSError as exc:
                messagebox.showerror('Erro ao salvar', str(exc), parent=self.window)
