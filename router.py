"""Atalho para comandos simples: resolve sem passar pelo LLM.

Em PC fraco isso faz toda a diferença: "abre o chrome" responde na hora,
em vez de esperar o modelo pensar. Se nada casar, devolve None e o LLM assume.
"""
import re

import tools


def _limpar(texto: str) -> str:
    t = texto.lower().strip()
    t = re.sub(r"^(?:ei |ok |olá |ola )?(?:oreo|óreo)[,!. ]+", "", t)
    return t.strip(" .!?,")


def tentar(texto: str):
    t = _limpar(texto)
    if not t:
        return None

    # --- lembrete com tempo: "me lembra de beber água daqui a 10 minutos"
    m = re.search(r"(?:daqui a|daqui|em)\s+(\d+)\s*(minutos?|min|horas?|h)\b", t)
    if m and re.search(r"lembr|avis", t):
        n = int(m.group(1))
        minutos = n * 60 if m.group(2).startswith("h") else n
        msg = re.sub(r"\s+", " ", f"{t[:m.start()]} {t[m.end():]}").strip()
        msg = re.sub(r"^(?:me\s+)?(?:lembra|lembre|lembrar|avisa|avise|avisar)(?:\s+(?:de|que|para|pra))?\s*", "", msg)
        return tools.lembrete(minutos, msg or "lembrete")

    # --- horas / data
    if re.search(r"\bque horas?\b|\bhoras? (?:são|sao)\b|\bque dia (?:é|e) hoje\b|\bdata de hoje\b", t):
        return tools.ver_horas()

    # --- volume
    if re.search(r"\bvolume\b", t) or re.search(r"\b(?:mut[ae]|silencia|mudo)\b", t):
        if re.search(r"\b(?:aument|sobe|suba|mais alto|maior)", t):
            return tools.ajustar_volume("aumentar")
        if re.search(r"\b(?:diminu|abaix|baix|reduz|menos|menor)", t):
            return tools.ajustar_volume("diminuir")
        if re.search(r"\b(?:mut|silenc|mudo)", t):
            return tools.ajustar_volume("mudo")

    # --- mídia
    if re.search(r"^(?:próxima|proxima|pula|pular|avança)(?: a| essa)?(?: música| musica| faixa)?$", t):
        return tools.controle_midia("proxima")
    if re.search(r"(?:música|musica|faixa) anterior|^volta(?: a)?(?: música| musica| faixa)?$", t):
        return tools.controle_midia("anterior")
    if re.search(r"^(?:pausa|pause|pausar|continua|continuar|retoma)(?: a| o)?(?: música| musica| som)?$|^d[aá] play$", t):
        return tools.controle_midia("tocar_pausar")

    # --- clima
    if re.search(r"\b(?:clima|previsão do tempo|previsao do tempo|temperatura|como (?:está|esta) o tempo)\b", t):
        t2 = re.sub(r"\b(?:hoje|agora)\b", "", t).strip()
        c = re.search(r"\b(?:em|de|para|no|na)\s+([a-zà-ú][a-zà-ú ]+)$", t2)
        cidade = c.group(1).strip() if c and c.group(1) not in ("hoje", "agora") else ""
        return tools.clima(cidade)

    # --- sistema
    if re.search(r"bloque\w*\s+(?:o |a )?(?:pc|computador|tela)", t):
        return tools.bloquear_pc()
    if re.search(r"\b(?:tira|tire|faz|faça|faca)\s+(?:um\s+)?print\b|captura de tela|screenshot", t):
        return tools.captura_tela()

    # --- arquivos
    m = re.match(r"^(?:procura|procure|busca|busque|encontra|encontre)\s+(?:o |um )?arquivo\s+(.+)$", t)
    if m:
        return tools.buscar_arquivo(m.group(1))
    m = re.match(r"^(?:abr[ae]|abrir)\s+(?:o |um )?arquivo\s+(.+)$", t)
    if m:
        return tools.abrir_arquivo(m.group(1))

    # --- anotações e memória
    m = re.match(r"^(?:anota|anote|anotar)\s+(?:que |isso:? )?(.+)$", t)
    if m:
        return tools.anotar(m.group(1))
    m = re.match(r"^(?:lembra|lembre|lembre-se|guarda|guarde|memoriza)\s+que\s+(.+)$", t)
    if m:
        return tools.guardar_memoria(m.group(1))

    # --- pesquisa
    m = re.match(r"^(?:pesquis[ae]|pesquisar|busca|busque|procura|procure)\s+(?:na (?:web|internet) )?(?:por |sobre )?(.+)$", t)
    if m:
        return tools.pesquisar_na_web(m.group(1))

    # --- abrir programa / site
    m = re.match(r"^(?:abr[ae]|abrir|inicia|inicie|iniciar|executa|execute)\s+(?:o |a |os |as |um |uma )?(.+)$", t)
    if m:
        alvo = m.group(1).strip()
        if tools.programa_existe(alvo):
            return tools.abrir_programa(alvo)
        if tools.site_conhecido(alvo):
            return tools.abrir_site(alvo)

    return None
