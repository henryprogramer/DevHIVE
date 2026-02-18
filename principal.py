# principal.py
import sys
from PyQt5.QtWidgets import QApplication

from banco.init_db import inicializar_banco
from interface.janelas.tela_login import TelaLogin
from interface.interface import InterfaceWindow

class AppController:
    def __init__(self):
        # inicializa banco (tabelas) antes de criar QApplication para testes headless também
        inicializar_banco()

        self.app = QApplication(sys.argv)
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
