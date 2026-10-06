"""Faz o OREO iniciar sozinho com o Windows (em segundo plano, na bandeja).

  python instalar_inicializacao.py            ativa
  python instalar_inicializacao.py --remover  desativa

Rode com o Python da venv (venv ativada) para que o caminho certo seja registrado.
"""
import sys
from pathlib import Path

CHAVE = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOME = "OREO"


def main():
    import winreg
    if "--remover" in sys.argv:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHAVE, 0, winreg.KEY_SET_VALUE) as k:
            try:
                winreg.DeleteValue(k, NOME)
                print("OREO removido da inicialização.")
            except FileNotFoundError:
                print("OREO não estava na inicialização.")
        return

    py = Path(sys.executable)
    pythonw = py.with_name("pythonw.exe")           # sem janela de terminal
    if not pythonw.exists():
        pythonw = py
    main_py = Path(__file__).resolve().with_name("main.py")
    comando = f'"{pythonw}" "{main_py}" --bandeja'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHAVE, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, NOME, 0, winreg.REG_SZ, comando)
    print("OREO vai iniciar com o Windows. Comando registrado:\n", comando)
    print("Lembre-se: o Ollama também precisa iniciar com o Windows (o instalador dele já faz isso).")


if __name__ == "__main__":
    main()
