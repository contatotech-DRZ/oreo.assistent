"""Loop de voz: espera a palavra de ativação (ou tecla), ouve o comando e responde."""
import time

import config
import stt
import tts


def bip(freq=900, ms=120):
    try:
        import winsound
        winsound.Beep(freq, ms)
    except Exception:
        pass


def ouvir_comando(cancelar=None) -> str:
    audio = stt.gravar_frase(esperar_fala=6.0, max_seg=15.0, cancelar=cancelar)
    return stt.transcrever(audio) if audio is not None else ""


def _esperar_tecla(parar):
    import keyboard
    while not parar.is_set():
        if keyboard.is_pressed(config.HOTKEY):
            time.sleep(0.2)
            return True
        time.sleep(0.05)
    return False


def loop_voz(assistente, parar, pausado=None):
    print("Calibrando o microfone, fique em silêncio por 1 segundo...", flush=True)
    limiar = stt.calibrar()
    print(f"Limiar de voz: {limiar:.4f}. Carregando o reconhecimento de fala...", flush=True)
    stt._get_modelo()
    modo = (f"diga '{config.NOME_ASSISTENTE}' + o comando" if config.MODO_ATIVACAO == "palavra"
            else f"aperte {config.HOTKEY.upper()} e fale")
    print(f"{config.NOME_ASSISTENTE} pronto: {modo}.\n", flush=True)
    assistente._dizer(f"{config.NOME_ASSISTENTE} online.")

    while not parar.is_set() and not assistente.encerrar.is_set():
        if pausado is not None and pausado.is_set():
            time.sleep(0.5)
            continue
        try:
            if config.MODO_ATIVACAO == "tecla":
                if not _esperar_tecla(parar):
                    break
                bip()
                texto = ouvir_comando(parar.is_set)
            else:
                audio = stt.gravar_frase(esperar_fala=None, max_seg=8.0, cancelar=parar.is_set)
                if audio is None:
                    continue
                achou, resto = stt.procurar_palavra_ativacao(stt.transcrever(audio))
                if not achou:
                    continue
                if len(resto) >= 3:
                    texto = resto
                else:
                    bip()
                    texto = ouvir_comando(parar.is_set)
            if texto:
                assistente.processar(texto)
        except Exception as erro:
            print(f"[voz] erro: {type(erro).__name__}: {erro}", flush=True)
            time.sleep(1)
    parar.set()
