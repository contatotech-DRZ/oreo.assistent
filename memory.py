"""Memória de longo prazo do OREO.

Guarda fatos (ex: "meu irmão gosta de rock") num SQLite local. Poucos fatos são
sempre injetados na conversa; com muitos, busca os mais parecidos por significado
(embeddings do Ollama) ou, se isso falhar, por palavras em comum.
"""
import json
import math
import re
import sqlite3
import threading
import time

import config

_instancia = None


def obter():
    global _instancia
    if _instancia is None:
        _instancia = Memoria()
    return _instancia


def _cos(a, b):
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return num / den if den else 0.0


def _palavras(texto):
    return {p for p in re.findall(r"\w+", texto.lower()) if len(p) >= 4}


class Memoria:
    def __init__(self, caminho=None):
        self._lock = threading.Lock()
        self.db = sqlite3.connect(str(caminho or config.DATA_DIR / "memoria.db"), check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS fatos (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "texto TEXT NOT NULL, embedding TEXT, criado REAL)")
        self.db.commit()

    def _embed(self, texto):
        if not config.USAR_MEMORIA_SEMANTICA:
            return None
        try:
            import ollama
            r = ollama.embed(model=config.MODELO_EMBEDDING, input=texto)
            return list(r["embeddings"][0])
        except Exception:
            return None

    def lembrar(self, texto):
        emb = self._embed(texto)
        with self._lock:
            self.db.execute("INSERT INTO fatos (texto, embedding, criado) VALUES (?, ?, ?)",
                            (texto.strip(), json.dumps(emb) if emb else None, time.time()))
            self.db.commit()

    def todos(self):
        with self._lock:
            return [r[0] for r in self.db.execute("SELECT texto FROM fatos ORDER BY id")]

    def quantidade(self):
        with self._lock:
            return self.db.execute("SELECT COUNT(*) FROM fatos").fetchone()[0]

    def esquecer_tudo(self):
        with self._lock:
            self.db.execute("DELETE FROM fatos")
            self.db.commit()

    def relevantes(self, consulta, k=3, minimo=0.45):
        with self._lock:
            linhas = list(self.db.execute("SELECT texto, embedding FROM fatos"))
        if not linhas:
            return []
        if len(linhas) <= config.LIMITE_FATOS_DIRETOS:
            return [t for t, _ in linhas]

        emb = self._embed(consulta)
        if emb:
            pontuados = []
            for texto, e in linhas:
                if e:
                    pontuados.append((_cos(emb, json.loads(e)), texto))
            pontuados.sort(reverse=True)
            achados = [t for s, t in pontuados[:k] if s >= minimo]
            if achados:
                return achados

        # plano B: palavras em comum
        q = _palavras(consulta)
        pontuados = sorted(((len(q & _palavras(t)), t) for t, _ in linhas), reverse=True)
        return [t for s, t in pontuados[:k] if s > 0]
