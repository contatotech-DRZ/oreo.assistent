"""Ponto de entrada do OREO.

  python main.py              chat no terminal (com voz de saída)
  python main.py --voz        conversa por voz, no terminal
  python main.py --bandeja    conversa por voz, em segundo plano (ícone na bandeja)
  python main.py --teste-voz  testa só a voz de saída
  python main.py --teste-mic  testa só o microfone e a transcrição
"""
import argparse
import sys
import threading

import config


def _garantir_saida():
    # Com pythonw (sem janela) não existe stdout; mandamos tudo para um log.
    if sys.stdout is None or sys.stderr is None:
        log = open(config.DATA_DIR / "oreo.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or log
        sys.stderr = sys.stderr or log
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def modo_texto():
    from assistente import Assistente
    a = Assistente(falar=True)
    print(f"{config.NOME_ASSISTENTE} online. Digite 'sair' para encerrar.\n")
    while not a.encerrar.is_set():
        try:
            entrada = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not entrada:
            continue
        if entrada.lower() in ("sair", "exit"):
            break
        a.processar(entrada)


def modo_voz():
    from assistente import Assistente
    from voz import loop_voz
    parar = threading.Event()
    try:
        loop_voz(Assistente(falar=True), parar)
    except KeyboardInterrupt:
        parar.set()


def modo_bandeja():
    from assistente import Assistente
    from tray import executar_bandeja
    executar_bandeja(Assistente(falar=True))


def teste_voz():
    import tts
    tts.falar(f"Olá! Eu sou o {config.NOME_ASSISTENTE}. Se você está me ouvindo, a voz está funcionando.")
    tts.esperar()


def teste_mic():
    import stt
    print("Calibrando (silêncio por 1 segundo)...")
    print(f"Limiar: {stt.calibrar():.4f}")
    print("Fale uma frase agora...")
    audio = stt.gravar_frase(esperar_fala=8.0)
    if audio is None:
        print("Não ouvi nada. Verifique o microfone padrão do Windows.")
        return
    print("Transcrevendo (a primeira vez baixa o modelo, pode demorar)...")
    print("Entendi:", stt.transcrever(audio))


if __name__ == "__main__":
    _garantir_saida()
    p = argparse.ArgumentParser(description=f"{config.NOME_ASSISTENTE}, assistente local")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--voz", action="store_true")
    g.add_argument("--bandeja", action="store_true")
    g.add_argument("--teste-voz", action="store_true")
    g.add_argument("--teste-mic", action="store_true")
    args = p.parse_args()

    if args.voz:
        modo_voz()
    elif args.bandeja:
        modo_bandeja()
    elif args.teste_voz:
        teste_voz()
    elif args.teste_mic:
        teste_mic()
    else:
        modo_texto()
