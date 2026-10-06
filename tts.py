"""Voz de saída. Fala em segundo plano, frase por frase, numa fila.

Motores: "windows" (vozes do próprio Windows via pyttsx3) ou "piper" (mais natural).
Se o Piper falhar, cai automaticamente para a voz do Windows.
"""
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading

import config

_fila = queue.Queue()
_worker = None
_trava = threading.Lock()
_piper_quebrado = False


def _limpar(texto: str) -> str:
    texto = re.sub(r"[*_`#>~]+", "", texto)
    texto = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf]", "", texto)   # emojis
    return re.sub(r"\s+", " ", texto).strip()


def _falar_windows(texto: str):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass
    import pyttsx3
    motor = pyttsx3.init()
    motor.setProperty("rate", config.VELOCIDADE_VOZ)
    for voz in motor.getProperty("voices"):
        nome = (voz.name or "").lower()
        if any(p in nome for p in ("portug", "brazil", "maria", "daniel")):
            motor.setProperty("voice", voz.id)
            break
    motor.say(texto)
    motor.runAndWait()
    motor.stop()


def _falar_piper(texto: str):
    import winsound
    if not os.path.exists(config.PIPER_MODELO):
        raise FileNotFoundError(f"Modelo do Piper não encontrado: {config.PIPER_MODELO}")
    fd, caminho = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        subprocess.run([sys.executable, "-m", "piper", "--model", str(config.PIPER_MODELO),
                        "--output_file", caminho],
                       input=texto.encode("utf-8"), check=True, capture_output=True,
                       timeout=60, creationflags=flags)
        winsound.PlaySound(caminho, winsound.SND_FILENAME)
    finally:
        try:
            os.remove(caminho)
        except OSError:
            pass


def _falar_agora(texto: str):
    global _piper_quebrado
    if config.MOTOR_TTS == "piper" and not _piper_quebrado:
        try:
            _falar_piper(texto)
            return
        except Exception as erro:
            _piper_quebrado = True
            print(f"[tts] Piper falhou ({erro}). Usando a voz do Windows.", flush=True)
    _falar_windows(texto)


def _loop():
    while True:
        texto = _fila.get()
        try:
            _falar_agora(texto)
        except Exception as erro:
            print(f"[tts] erro ao falar: {erro}", flush=True)
        finally:
            _fila.task_done()


def falar(texto: str):
    """Coloca o texto na fila de fala e retorna na hora."""
    global _worker
    texto = _limpar(texto)
    if not texto:
        return
    with _trava:
        if _worker is None:
            _worker = threading.Thread(target=_loop, daemon=True)
            _worker.start()
    _fila.put(texto)


def esperar():
    """Bloqueia até o OREO terminar de falar tudo que está na fila."""
    _fila.join()
