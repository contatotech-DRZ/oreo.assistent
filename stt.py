"""Voz de entrada: grava do microfone, detecta o fim da frase e transcreve (faster-whisper)."""
import queue
import re
import time
from collections import deque

import config

TAXA = 16000
BLOCO = int(TAXA * 0.03)   # blocos de 30 ms

_modelo = None
_limiar = config.LIMIAR_MINIMO


def _get_modelo():
    global _modelo
    if _modelo is None:
        from faster_whisper import WhisperModel
        # 1ª vez baixa o modelo da internet; depois funciona offline
        _modelo = WhisperModel(config.WHISPER_MODELO, device="cpu", compute_type="int8")
    return _modelo


def _rms(bloco) -> float:
    import numpy as np
    return float(np.sqrt(np.mean(np.square(bloco))))


def calibrar(segundos: float = 1.0):
    """Mede o ruído de fundo para ajustar a sensibilidade. Fique em silêncio."""
    global _limiar
    import sounddevice as sd
    audio = sd.rec(int(TAXA * segundos), samplerate=TAXA, channels=1, dtype="float32")
    sd.wait()
    ruido = _rms(audio[:, 0])
    _limiar = max(config.LIMIAR_MINIMO, ruido * config.MULTIPLICADOR_RUIDO)
    return _limiar


def gravar_frase(esperar_fala=5.0, max_seg=15.0, silencio_fim=None, cancelar=None):
    """Grava uma frase. Retorna o áudio (numpy) ou None se ninguém falou.

    esperar_fala: segundos esperando alguém começar a falar (None = para sempre).
    cancelar: função que retorna True para abortar a espera.
    """
    import numpy as np
    import sounddevice as sd

    silencio_fim = silencio_fim or config.SILENCIO_FIM
    q = queue.Queue()
    pre = deque(maxlen=8)          # guarda ~240 ms antes da fala para não cortar o início
    blocos, falando, silencio = [], False, 0.0
    inicio, t_fala = time.time(), 0.0

    def cb(indata, frames, tempo, status):
        q.put(indata[:, 0].copy())

    with sd.InputStream(samplerate=TAXA, channels=1, dtype="float32", blocksize=BLOCO, callback=cb):
        while True:
            if cancelar and cancelar():
                return None
            try:
                bloco = q.get(timeout=0.5)
            except queue.Empty:
                continue
            nivel, agora = _rms(bloco), time.time()
            if not falando:
                if nivel > _limiar:
                    falando, t_fala = True, agora
                    blocos.extend(pre)
                    blocos.append(bloco)
                else:
                    pre.append(bloco)
                    if esperar_fala is not None and agora - inicio > esperar_fala:
                        return None
            else:
                blocos.append(bloco)
                silencio = 0.0 if nivel > _limiar else silencio + BLOCO / TAXA
                if silencio >= silencio_fim or agora - t_fala > max_seg:
                    break

    audio = np.concatenate(blocos)
    return audio if len(audio) / TAXA > 0.4 else None


def transcrever(audio) -> str:
    segmentos, _ = _get_modelo().transcribe(audio, language="pt", beam_size=1,
                                            initial_prompt=config.NOME_ASSISTENTE)
    return " ".join(s.text.strip() for s in segmentos).strip()


def procurar_palavra_ativacao(texto: str):
    """Retorna (achou, resto). 'OREO, abre o chrome' -> (True, 'abre o chrome')."""
    m = re.search(config.PALAVRAS_ATIVACAO, texto, flags=re.IGNORECASE)
    if not m:
        return False, ""
    return True, texto[m.end():].strip(" ,.!?;:-")
