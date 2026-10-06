# OREO

OREO é um assistente pessoal (uma IA) que roda **100% no seu PC**, sem nuvem e sem custo. Feito em Python, com LLM local via [Ollama](https://ollama.com).

Ele escuta ("OREO, abre o Chrome"), entende, executa ações no computador e responde falando.

## O que ele faz

- Conversa em português com memória da conversa
- Fala as respostas em voz alta (voz do Windows ou Piper)
- Ouve pela palavra de ativação "OREO" ou por uma tecla (F9)
- Abre programas e sites, controla volume e mídia, bloqueia o PC, tira print
- Pesquisa no Google, informa horas e clima, busca e abre arquivos
- Cria lembretes falados e anotações
- Memória de longo prazo: "OREO, lembra que meu gato se chama Mingau"
- Roda em segundo plano na bandeja do sistema e pode iniciar com o Windows

Comandos simples (abrir app, volume, horas...) passam por um **router** que responde na hora, sem esperar o LLM. Isso deixa tudo bem mais rápido em PC modesto.

## Requisitos

- Windows 10/11, Python 3.10 a 3.12
- [Ollama](https://ollama.com) instalado
- 16 GB de RAM. GPU não é obrigatória (o OREO foi pensado para rodar na CPU)
- Microfone e caixas de som ou fone

## Instalação

```powershell
git clone <url-do-repositorio>
cd oreo
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

ollama pull qwen2.5:3b
ollama pull nomic-embed-text     # memória por significado (opcional)
```

Se o PowerShell bloquear a ativação da venv:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Primeiro uso (nesta ordem)

```powershell
python main.py --teste-voz    # 1. ele fala?
python main.py                # 2. chat no terminal funciona?
python main.py --teste-mic    # 3. o microfone e a transcrição funcionam?
python main.py --voz          # 4. conversa por voz
python main.py --bandeja      # 5. segundo plano, ícone na bandeja
```

Na primeira vez que usar o microfone, o faster-whisper baixa o modelo de reconhecimento (precisa de internet uma vez só).

## Iniciar com o Windows

```powershell
python instalar_inicializacao.py            # ativa
python instalar_inicializacao.py --remover  # desativa
```

Rode com a venv ativada. O Ollama também precisa iniciar com o Windows (o instalador dele já faz isso).

## Configuração (`config.py`)

| Opção | Para quê |
|---|---|
| `MODELO` | `qwen2.5:3b` (padrão), `qwen2.5:1.5b` se estiver lento, `qwen2.5:7b` se tiver PC forte |
| `NOME_USUARIO` / `CIDADE_PADRAO` | personalizam respostas e o clima |
| `MODO_ATIVACAO` | `"palavra"` (diz OREO) ou `"tecla"` (aperta `HOTKEY`) |
| `WHISPER_MODELO` | `tiny` (rápido), `base` (padrão), `small` (mais preciso, mais lento) |
| `PALAVRAS_ATIVACAO` | variações do nome que o Whisper pode escrever |
| `MOTOR_TTS` | `"windows"` ou `"piper"` |
| `USAR_ROUTER` | atalho sem LLM para comandos simples |

## Voz natural com Piper (opcional)

```powershell
pip install piper-tts
```
Baixe uma voz em português do Brasil (por exemplo `pt_BR-faber-medium.onnx` e o `.onnx.json` correspondente) do repositório `rhasspy/piper-voices` no Hugging Face, coloque na pasta `models/` e troque `MOTOR_TTS = "piper"` no `config.py`. Se o Piper falhar, o OREO volta sozinho para a voz do Windows.

## Adicionar programas

Crie `data/programas.json`:
```json
{ "meu jogo": "C:\\Games\\jogo\\jogo.exe", "word": "winword" }
```

## Adicionar uma ferramenta nova

1. Escreva a função em `tools.py` com docstring e dicas de tipo (o LLM lê isso)
2. Adicione em `DISPONIVEIS` (e em `LISTA_LLM` se o modelo deve poder chamá-la)
3. Opcional: crie um padrão no `router.py` para resposta instantânea

Modelos pequenos erram mais com muitas ferramentas, por isso `LISTA_LLM` é menor que `DISPONIVEIS`.

## Segurança

- O OREO só executa o que está em `tools.py`; ele não roda comandos arbitrários
- Programas abríveis ficam numa lista fechada
- `abrir_arquivo` recusa executáveis e scripts
- Não há ferramenta de desligar o PC de propósito. Se adicionar, peça confirmação por voz

## Problemas comuns

| Sintoma | O que fazer |
|---|---|
| "Não consegui falar com o Ollama" | Abra o Ollama (ícone na bandeja) |
| Resposta muito lenta | Use `qwen2.5:1.5b`, feche programas pesados |
| Não acha a palavra OREO | Rode `--teste-mic`, veja como o Whisper escreve e ajuste `PALAVRAS_ATIVACAO`, ou use `MODO_ATIVACAO = "tecla"` |
| Ativa com ruído/TV | Aumente `MULTIPLICADOR_RUIDO` ou use o modo tecla |
| Voz em inglês | Instale "Português (Brasil)" em Configurações > Hora e idioma > Fala |
| Não chama as ferramentas | Modelo pequeno demais; o router cobre o básico, ou teste o 7b |
| Erro no `keyboard` | Só é usado no modo tecla; tente abrir o terminal como administrador |

## Testes

```powershell
python -m unittest discover tests
```

## Estrutura

```
oreo/
├── main.py                    # ponto de entrada e modos
├── config.py                  # todas as configurações
├── assistente.py              # orquestra um turno (router, LLM, memória, fala)
├── brain.py                   # LLM via Ollama, streaming e ferramentas
├── router.py                  # atalho para comandos simples
├── tools.py                   # ações no PC
├── memory.py                  # memória de longo prazo (SQLite)
├── stt.py                     # microfone e transcrição (faster-whisper)
├── tts.py                     # voz de saída
├── voz.py                     # loop de escuta e palavra de ativação
├── tray.py                    # ícone na bandeja
├── instalar_inicializacao.py  # iniciar com o Windows
├── tests/
└── requirements.txt
```

## Roadmap

- [x] Cérebro local, chat, ferramentas, voz de saída
- [x] Voz de entrada, palavra de ativação, memória, bandeja, inicialização
- [ ] Testes em hardware real e ajustes finos
- [ ] Interrupção de fala ("OREO, para")
- [ ] Lembretes que sobrevivem ao reinício
- [ ] Controle de volume por aplicativo (pycaw)

## Licença

MIT
