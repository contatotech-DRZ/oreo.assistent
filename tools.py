"""Ferramentas que o OREO pode executar no PC.

Cada função vira uma "ferramenta" para o LLM. O docstring e as dicas de tipo
são o que o modelo lê para saber quando e como chamar, então mantenha-os claros.
"""
import json
import os
import subprocess
import threading
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

import config

# ---------------------------------------------------------------- programas
# Só o que estiver aqui (ou em data/programas.json) pode ser aberto.
PROGRAMAS_BASE = {
    "calculadora": "calc",
    "bloco de notas": "notepad",
    "explorador": "explorer",
    "explorador de arquivos": "explorer",
    "paint": "mspaint",
    "chrome": "chrome",
    "edge": "msedge",
    "spotify": "spotify:",
    "discord": "discord:",
    "steam": "steam:",
    "terminal": "wt",
    "vscode": "code",
    "configurações": "ms-settings:",
    "gerenciador de tarefas": "taskmgr",
}

SITES = {
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "netflix": "https://www.netflix.com",
    "whatsapp": "https://web.whatsapp.com",
    "maps": "https://maps.google.com",
}

EXTENSOES_BLOQUEADAS = {".exe", ".bat", ".cmd", ".ps1", ".msi", ".vbs", ".js", ".lnk", ".scr", ".com"}
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def _programas():
    progs = dict(PROGRAMAS_BASE)
    extra = config.DATA_DIR / "programas.json"
    if extra.exists():
        try:
            with open(extra, encoding="utf-8") as f:
                progs.update({k.lower(): v for k, v in json.load(f).items()})
        except Exception:
            pass
    return progs


def programa_existe(nome: str) -> bool:
    return nome.lower().strip() in _programas()


def site_conhecido(nome: str) -> bool:
    n = nome.lower().strip()
    return n in SITES or ("." in n and " " not in n)


def _pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = False
    return pyautogui


# ---------------------------------------------------------------- ferramentas
def ver_horas() -> str:
    """Retorna o dia da semana, a data e a hora atuais."""
    agora = datetime.now()
    return f"Hoje é {DIAS[agora.weekday()]}, {agora:%d/%m/%Y}, e são {agora:%H:%M}."


def abrir_programa(nome: str) -> str:
    """Abre um programa no computador.

    Args:
        nome: nome do programa, por exemplo calculadora, bloco de notas, chrome, spotify.
    """
    progs = _programas()
    comando = progs.get(nome.lower().strip())
    if not comando:
        return f"Não conheço o programa {nome}. Posso abrir: {', '.join(sorted(progs))}."
    if os.name != "nt":
        return "Abrir programas só funciona no Windows."
    subprocess.Popen(f'start "" "{comando}"', shell=True)
    return f"Abrindo {nome}."


def abrir_site(site: str) -> str:
    """Abre um site no navegador padrão.

    Args:
        site: nome conhecido (youtube, gmail, github) ou endereço, por exemplo exemplo.com.br.
    """
    s = site.lower().strip()
    url = SITES.get(s)
    if not url:
        if " " in s or "." not in s:
            return f"Não entendi qual site abrir: {site}."
        url = s if s.startswith("http") else f"https://{s}"
    if not url.startswith(("http://", "https://")):
        return "Só abro endereços http ou https."
    webbrowser.open(url)
    return f"Abrindo {site}."


def pesquisar_na_web(busca: str) -> str:
    """Pesquisa algo no Google usando o navegador padrão.

    Args:
        busca: o texto a ser pesquisado.
    """
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote_plus(busca))
    return f"Pesquisando por {busca}."


def ajustar_volume(acao: str, quantidade: int = 10) -> str:
    """Ajusta o volume do computador.

    Args:
        acao: 'aumentar', 'diminuir' ou 'mudo'.
        quantidade: quanto mudar, de 2 a 100 (cada 2 equivale a um passo).
    """
    pag = _pyautogui()
    if acao == "mudo":
        pag.press("volumemute")
        return "Alternei o mudo."
    if acao not in ("aumentar", "diminuir"):
        return "Ação de volume inválida."
    passos = max(1, int(float(quantidade)) // 2)
    pag.press("volumeup" if acao == "aumentar" else "volumedown", presses=passos)
    return f"Volume {'aumentado' if acao == 'aumentar' else 'diminuído'}."


def controle_midia(acao: str) -> str:
    """Controla a música ou vídeo que está tocando.

    Args:
        acao: 'tocar_pausar', 'proxima' ou 'anterior'.
    """
    teclas = {"tocar_pausar": "playpause", "proxima": "nexttrack", "anterior": "prevtrack"}
    if acao not in teclas:
        return "Ação de mídia inválida."
    _pyautogui().press(teclas[acao])
    return "Feito."


_CODIGOS_CLIMA = {
    0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado", 3: "nublado",
    45: "com neblina", 48: "com neblina", 51: "com garoa fraca", 53: "com garoa", 55: "com garoa forte",
    61: "com chuva fraca", 63: "com chuva", 65: "com chuva forte", 80: "com pancadas de chuva",
    81: "com pancadas de chuva", 82: "com pancadas fortes de chuva", 95: "com trovoadas",
    96: "com trovoadas e granizo", 99: "com trovoadas e granizo",
}


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "OREO/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def clima(cidade: str = "") -> str:
    """Informa o clima atual de uma cidade (precisa de internet).

    Args:
        cidade: nome da cidade. Se vazio, usa a cidade padrão configurada.
    """
    cidade = (cidade or config.CIDADE_PADRAO).strip()
    if not cidade:
        return "Me diga de qual cidade você quer saber o clima."
    try:
        geo = _get_json("https://geocoding-api.open-meteo.com/v1/search?" +
                        urllib.parse.urlencode({"name": cidade, "count": 1, "language": "pt"}))
        if not geo.get("results"):
            return f"Não encontrei a cidade {cidade}."
        r = geo["results"][0]
        w = _get_json("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
            "latitude": r["latitude"], "longitude": r["longitude"], "timezone": "auto",
            "current": "temperature_2m,apparent_temperature,weather_code"}))
        c = w["current"]
        desc = _CODIGOS_CLIMA.get(c["weather_code"], "com tempo variável")
        return (f"Em {r['name']} agora faz {round(c['temperature_2m'])} graus, "
                f"sensação de {round(c['apparent_temperature'])}, {desc}.")
    except Exception:
        return "Não consegui consultar o clima. Verifique a internet."


def lembrete(minutos: int, mensagem: str) -> str:
    """Cria um lembrete falado após alguns minutos.

    Args:
        minutos: daqui a quantos minutos avisar.
        mensagem: o que lembrar.
    """
    minutos = max(1, int(float(minutos)))

    def disparar():
        import tts
        tts.falar(f"Lembrete: {mensagem}")

    t = threading.Timer(minutos * 60, disparar)
    t.daemon = True
    t.start()
    return f"Combinado, aviso em {minutos} minutos: {mensagem}. Se o OREO for fechado, o lembrete se perde."


def anotar(texto: str) -> str:
    """Salva uma anotação no arquivo de notas.

    Args:
        texto: o que anotar.
    """
    with open(config.DATA_DIR / "notas.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m/%Y %H:%M}] {texto}\n")
    return "Anotado."


def guardar_memoria(fato: str) -> str:
    """Guarda um fato sobre o usuário para lembrar no futuro, como gostos e rotina.

    Args:
        fato: o fato a lembrar, escrito em frase completa.
    """
    import memory
    memory.obter().lembrar(fato)
    return "Vou lembrar disso."


def _pastas_usuario():
    home = Path.home()
    nomes = ["Documents", "Desktop", "Downloads", "Pictures", "Videos", "Music"]
    pastas = [home / n for n in nomes]
    pastas += [home / "OneDrive" / n for n in nomes]
    return [p for p in pastas if p.exists()]


def _procurar(nome: str, limite: int = 5):
    import time
    nome = nome.lower().strip()
    achados, fim = [], time.time() + 6
    for pasta in _pastas_usuario():
        for raiz, _, arquivos in os.walk(pasta):
            for a in arquivos:
                if nome in a.lower():
                    achados.append(Path(raiz) / a)
                    if len(achados) >= limite:
                        return achados
            if time.time() > fim:
                return achados
    return achados


def buscar_arquivo(nome: str) -> str:
    """Procura arquivos pelo nome nas pastas do usuário (documentos, downloads, desktop, imagens).

    Args:
        nome: parte do nome do arquivo.
    """
    achados = _procurar(nome)
    if not achados:
        return f"Não achei nenhum arquivo com {nome} no nome."
    return f"Encontrei {len(achados)}: " + "; ".join(a.name for a in achados)


def abrir_arquivo(nome: str) -> str:
    """Abre um arquivo (documento, imagem, vídeo) pelo nome. Não abre programas executáveis.

    Args:
        nome: parte do nome do arquivo.
    """
    for a in _procurar(nome, limite=20):
        if a.suffix.lower() not in EXTENSOES_BLOQUEADAS:
            os.startfile(str(a))
            return f"Abrindo {a.name}."
    return f"Não achei um arquivo seguro com {nome} no nome."


def bloquear_pc() -> str:
    """Bloqueia a tela do computador."""
    import ctypes
    ctypes.windll.user32.LockWorkStation()
    return "Bloqueando o computador."


def captura_tela() -> str:
    """Tira um print da tela e salva na pasta Imagens."""
    pasta = Path.home() / "Pictures"
    pasta.mkdir(exist_ok=True)
    caminho = pasta / f"oreo_print_{datetime.now():%Y%m%d_%H%M%S}.png"
    _pyautogui().screenshot(str(caminho))
    return f"Print salvo na pasta Imagens."


# Todas as ferramentas que o router pode chamar:
DISPONIVEIS = {f.__name__: f for f in [
    ver_horas, abrir_programa, abrir_site, pesquisar_na_web, ajustar_volume, controle_midia,
    clima, lembrete, anotar, guardar_memoria, buscar_arquivo, abrir_arquivo, bloquear_pc, captura_tela,
]}

# Ferramentas que o LLM enxerga. Poucas = modelo pequeno erra menos.
# Com modelo maior (7b+), pode trocar por: list(DISPONIVEIS.values())
LISTA_LLM = [ver_horas, abrir_programa, abrir_site, pesquisar_na_web, ajustar_volume,
             clima, lembrete, guardar_memoria, anotar, buscar_arquivo]
