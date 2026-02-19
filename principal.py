# principal.py
import sys
from PyQt5.QtWidgets import QApplication

from banco.init_db import inicializar_banco

from interface.janelas.tela_login import TelaLogin
from interface.interface import InterfaceWindow
from interface.theme_engine import apply_palette, build_theme_tokens, load_active_theme_record


def aplicar_tema_global(app):
    """
    Busca tema ativo no banco e aplica paleta base para reduzir inconsistências
    de cores entre login e interface principal.
    """
    theme = load_active_theme_record()
    if not theme:
        return

    tokens = build_theme_tokens(theme)
    apply_palette(app, tokens)


class AppController:
    def __init__(self):
        # 1️⃣ Inicializa banco
        inicializar_banco()

        # 2️⃣ Cria aplicação
        self.app = QApplication(sys.argv)

        # 3️⃣ Aplica tema ativo automaticamente
        aplicar_tema_global(self.app)

        # 4️⃣ Abre tela de login
        self.login = TelaLogin(self.usuario_logado)
        self.login.show()

    def usuario_logado(self, dados_usuario):
        self.main_window = InterfaceWindow(dados_usuario)
        self.main_window.show()
        self.login.close()

    def run(self):
        sys.exit(self.app.exec())


def main():
    controller = AppController()
    controller.run()


if __name__ == "__main__":
    main()
