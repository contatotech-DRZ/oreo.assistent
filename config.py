"""Configurações do OREO. Mexa aqui antes de mexer no resto do código."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"          # memória, notas, logs (ignorado pelo git)
DATA_DIR.mkdir(exist_ok=True)

# ---------- Identidade ----------
NOME_ASSISTENTE = "OREO"
NOME_USUARIO = ""        # ex: "Pedro". Se preencher, o OREO chama pelo nome
CIDADE_PADRAO = ""       # ex: "Salvador". Usada quando perguntam o clima sem cidade

# ---------- Cérebro (LLM via Ollama) ----------
MODELO = "qwen2.5:3b"            # PC fraco: 3b. Se ficar lento: "qwen2.5:1.5b"
MODELO_EMBEDDING = "nomic-embed-text"
OPCOES_LLM = {"num_ctx": 2048, "temperature": 0.6}   # contexto menor = mais rápido
MANTER_MODELO_NA_RAM = "30m"     # evita recarregar o modelo a cada pergunta
MAX_HISTORICO = 10               # quantas mensagens recentes o OREO lembra na conversa
USAR_ROUTER = True               # comandos simples sem passar pelo LLM (bem mais rápido)

SYSTEM_PROMPT = (
    f"Você é o {NOME_ASSISTENTE}, um assistente pessoal que roda no computador do usuário. "
    "Seja educado, objetivo e levemente bem-humorado. "
    "Responda sempre em português do Brasil, com frases curtas, pois suas respostas são faladas em voz alta. "
    "Não use markdown, listas, emojis nem asteriscos. "
    "Quando o usuário pedir uma ação no computador, use as ferramentas disponíveis. "
    "Nunca invente que executou algo sem chamar a ferramenta."
)

# ---------- Memória ----------
USAR_MEMORIA_SEMANTICA = True    # busca por significado (precisa do nomic-embed-text)
LIMITE_FATOS_DIRETOS = 5         # até esse número de fatos, injeta todos sem busca

# ---------- Voz de saída ----------
MOTOR_TTS = "windows"            # "windows" (pyttsx3) ou "piper" (mais natural, ver README)
VELOCIDADE_VOZ = 185
PIPER_MODELO = BASE_DIR / "models" / "pt_BR-faber-medium.onnx"

# ---------- Voz de entrada ----------
MODO_ATIVACAO = "palavra"        # "palavra" (diz "OREO, ...") ou "tecla" (aperta a HOTKEY)
HOTKEY = "f9"
WHISPER_MODELO = "base"          # "tiny" = mais rápido, "small" = mais preciso
# Whisper às vezes escreve o nome de formas diferentes. Adicione variações que aparecerem.
PALAVRAS_ATIVACAO = r"\b(?:oreo|óreo|oreu|orio|o reo|ó reo)\b"
LIMIAR_MINIMO = 0.012            # sensibilidade mínima do microfone
MULTIPLICADOR_RUIDO = 3.0        # quão acima do ruído de fundo conta como "fala"
SILENCIO_FIM = 0.8               # segundos de silêncio para considerar que a frase acabou
