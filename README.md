# Conecta USB

Aplicativo para Windows de diagnóstico USB e atendimento de aparelhos com senha esquecida.

## Download para Windows

**[Baixar Conecta para Windows 64 bits](https://github.com/Bneto-0/conecta-usb/releases/latest/download/Conecta-Windows-x64.zip)**

1. Baixe o ZIP e extraia toda a pasta.
2. Abra `Conecta.exe` dentro da pasta `Conecta`.
3. Não mova o executável sozinho: a pasta `_internal` precisa permanecer ao lado dele.

Não é necessário instalar Python. O executável desta primeira versão não possui assinatura digital. Consulte a origem e o SHA256 publicado na versão antes de executar.

## Recursos

- Consulta de interfaces de celular reconhecidas pelo Windows.
- Relatório de diagnóstico em JSON, sem número de série.
- Cadastro de atendimento com modelo, bloqueio, conta vinculada, backup, preferência sobre dados e autorização declarada.
- Orientações e links para suporte oficial de Android, Apple e Microsoft.
- Interface escura com menu lateral e painel de atendimento.
- Visualização da tela Android dentro do aplicativo, usando scrcpy, sem áudio, gravação ou controle pelo mouse.

O espelhamento exige depuração USB e autorização no próprio aparelho. O cadastro não substitui uma autorização específica antes de procedimentos com perda de dados. Não informe senhas ou chaves nos campos.

## Limites

O programa não descobre senhas, não remove padrões, não contorna bloqueios de conta e não formata dispositivos. Status USB OK não significa acesso aos arquivos. Não há espelhamento de iPhone ou computador nesta versão.

Os relatórios são salvos apenas no local escolhido. Se esse local for uma pasta sincronizada, o serviço de sincronização poderá enviar os arquivos para a nuvem. O botão de guia oficial abre o navegador. Não há envio automático de cadastros pelo Conecta.

## Código e compilação

Requer Windows 64 bits e Python 3.13 com Tkinter. Para executar o código: `python app.py`.

Para gerar a distribuição, execute `build.ps1` no PowerShell. O script baixa o scrcpy 4.1 da distribuição oficial, verifica seu SHA256 e utiliza o PyInstaller. A saída estará em `dist/Conecta`.

## Componentes de terceiros

O pacote preserva os arquivos da distribuição oficial do [scrcpy 4.1](https://github.com/Genymobile/scrcpy/releases/tag/v4.1), incluindo sua licença. Consulte `THIRD-PARTY.md` e `tools/scrcpy-win64-v4.1/LICENSE.txt` (ou `_internal/tools/...` no aplicativo compilado).
