"""Ícone na bandeja do sistema: OREO rodando em segundo plano."""
import threading

import pystray
from PIL import Image, ImageDraw

import config
from voz import loop_voz


def _icone(ativo: bool) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 60, 60), fill=(30, 30, 30, 255))
    d.ellipse((18, 18, 46, 46), fill=(0, 200, 120, 255) if ativo else (150, 150, 150, 255))
    return img


def executar_bandeja(assistente):
    parar, pausado = threading.Event(), threading.Event()
    threading.Thread(target=loop_voz, args=(assistente, parar, pausado), daemon=True).start()

    def alternar(icone, item):
        pausado.clear() if pausado.is_set() else pausado.set()
        icone.icon = _icone(not pausado.is_set())

    def sair(icone, item):
        parar.set()
        icone.stop()

    def vigiar(icone):
        icone.visible = True
        parar.wait()          # se o usuário disser "tchau", fecha a bandeja também
        icone.stop()

    menu = pystray.Menu(
        pystray.MenuItem(lambda item: "Retomar escuta" if pausado.is_set() else "Pausar escuta", alternar),
        pystray.MenuItem("Sair", sair),
    )
    pystray.Icon(config.NOME_ASSISTENTE, _icone(True), f"{config.NOME_ASSISTENTE} (escutando)",
                 menu).run(setup=lambda i: threading.Thread(target=vigiar, args=(i,), daemon=True).start())
