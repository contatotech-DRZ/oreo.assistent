"""Cérebro: conversa com o LLM (Ollama), com streaming e chamada de ferramentas."""
from datetime import datetime

import ollama

import config
import tools


class Cerebro:
    def __init__(self):
        self.historico = []
        self.suporta_ferramentas = True

    def _sistema(self, memoria_ctx: str) -> str:
        s = config.SYSTEM_PROMPT
        if config.NOME_USUARIO:
            s += f" O usuário se chama {config.NOME_USUARIO}."
        s += f" Agora são {datetime.now():%H:%M} do dia {datetime.now():%d/%m/%Y}."
        if memoria_ctx:
            s += "\n\nCoisas que você sabe sobre o usuário:\n" + memoria_ctx
        return s

    def _mensagens(self, memoria_ctx: str):
        recentes = self.historico[-config.MAX_HISTORICO:]
        # nunca começar o recorte no meio de uma chamada de ferramenta
        while recentes and recentes[0]["role"] != "user":
            recentes = recentes[1:]
        return [{"role": "system", "content": self._sistema(memoria_ctx)}] + recentes

    def _chamar(self, mensagens):
        kwargs = dict(model=config.MODELO, messages=mensagens, stream=True,
                      options=config.OPCOES_LLM, keep_alive=config.MANTER_MODELO_NA_RAM)
        if self.suporta_ferramentas:
            kwargs["tools"] = tools.LISTA_LLM
        try:
            return ollama.chat(**kwargs)
        except ollama.ResponseError as erro:
            if "tools" in str(erro).lower() and self.suporta_ferramentas:
                self.suporta_ferramentas = False   # modelo sem suporte: segue só conversando
                kwargs.pop("tools")
                return ollama.chat(**kwargs)
            raise

    def responder_stream(self, texto_usuario: str, memoria_ctx: str = ""):
        """Gera a resposta em pedaços de texto. Executa ferramentas quando o modelo pedir."""
        self.historico.append({"role": "user", "content": texto_usuario})

        for _ in range(4):  # no máximo 4 rodadas de ferramentas por pergunta
            conteudo, chamadas = "", []
            for pedaco in self._chamar(self._mensagens(memoria_ctx)):
                msg = pedaco.message
                if msg.content:
                    conteudo += msg.content
                    yield msg.content
                if msg.tool_calls:
                    chamadas.extend(msg.tool_calls)

            if not chamadas:
                self.historico.append({"role": "assistant", "content": conteudo})
                return

            self.historico.append({
                "role": "assistant", "content": conteudo,
                "tool_calls": [{"function": {"name": c.function.name,
                                             "arguments": dict(c.function.arguments)}} for c in chamadas],
            })
            for c in chamadas:
                nome = c.function.name
                try:
                    resultado = tools.DISPONIVEIS[nome](**dict(c.function.arguments))
                except Exception as erro:
                    resultado = f"Erro ao executar {nome}: {erro}"
                self.historico.append({"role": "tool", "tool_name": nome, "content": str(resultado)})

        yield "Desculpe, me enrolei tentando fazer isso."
