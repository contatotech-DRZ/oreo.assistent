"""Orquestra um turno: texto -> (router | LLM + memória) -> fala."""
import re
import threading

import config
import memory
import router
import tts
from brain import Cerebro

_FIM_FRASE = re.compile(r"(?<=[.!?…])\s+|\n+")
_ENCERRAR = re.compile(r"^(?:tchau|encerrar|encerra|pode dormir|até mais|ate mais)\b", re.IGNORECASE)


class Assistente:
    def __init__(self, falar: bool = True):
        self.cerebro = Cerebro()
        self.memoria = memory.obter()
        self.falar = falar
        self.encerrar = threading.Event()

    def _dizer(self, texto: str):
        print(f"{config.NOME_ASSISTENTE}: {texto}\n", flush=True)
        if self.falar:
            tts.falar(texto)
            tts.esperar()

    def processar(self, texto: str):
        print(f"Você: {texto}", flush=True)

        if _ENCERRAR.match(texto.strip()):
            self._dizer("Até mais!")
            self.encerrar.set()
            return

        if config.USAR_ROUTER:
            try:
                rapida = router.tentar(texto)
            except Exception as erro:
                rapida = f"Tive um problema ao executar isso: {erro}"
            if rapida is not None:
                self._dizer(rapida)
                return

        try:
            fatos = self.memoria.relevantes(texto)
            ctx = "\n".join(f"- {f}" for f in fatos)
            buffer = ""
            print(f"{config.NOME_ASSISTENTE}: ", end="", flush=True)
            for pedaco in self.cerebro.responder_stream(texto, ctx):
                print(pedaco, end="", flush=True)
                buffer += pedaco
                partes = _FIM_FRASE.split(buffer)
                for frase in partes[:-1]:      # fala cada frase assim que ela termina
                    if self.falar:
                        tts.falar(frase)
                buffer = partes[-1]
            if buffer.strip() and self.falar:
                tts.falar(buffer)
            print("\n", flush=True)
            if self.falar:
                tts.esperar()
        except Exception as erro:
            print()
            msg = ("Não consegui falar com o Ollama. Ele está aberto? "
                   f"Detalhe: {type(erro).__name__}")
            self._dizer(msg)
