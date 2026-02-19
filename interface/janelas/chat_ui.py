# interface/janelas/chat_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFrame,
    QTabWidget, QListWidget,
    QFormLayout, QDialog, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from banco.controles.chat_mestre.controle_chat import ChatController
from banco.controles.chat_mestre.controle_comando import ComandoController


# ======================================================
# Bolha de Mensagem
# ======================================================
class ChatBubble(QFrame):
    def __init__(self, texto: str, remetente="user"):
        super().__init__()

        self.setObjectName("chatBubble")
        self.setProperty("sender", remetente)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        label = QLabel(texto)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(label)

        if remetente == "user":
            self.setStyleSheet(
                """
                QFrame#chatBubble[sender="user"] {
                    background-color: rgba(70, 130, 255, 0.28);
                    border-radius: 12px;
                    padding: 8px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QFrame#chatBubble[sender="bot"] {
                    background-color: rgba(255, 255, 255, 0.06);
                    border-radius: 12px;
                    padding: 8px;
                }
                """
            )


# ======================================================
# Widget Principal
# ======================================================
class MainWidget(QWidget):

    def __init__(self, dados_usuario=None):
        super().__init__()

        self.dados_usuario = dados_usuario or {}
        self.nome_usuario = self.dados_usuario.get("nome", "Usuário")

        # ✅ CORRETO
        self.session_id = ChatController.obter_ou_criar_sessao(self.nome_usuario)

        self.init_ui()
        self.carregar_historico()

    # ======================================================
    # UI BASE
    # ======================================================
    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel(f"Chat - {self.nome_usuario}")
        header.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # Aba Chat
        self.chat_tab = QWidget()
        self.tabs.addTab(self.chat_tab, "Chat")
        self.init_chat_ui()

        # Aba Comandos
        self.comandos_tab = QWidget()
        self.tabs.addTab(self.comandos_tab, "Gerenciador de Comandos")
        self.init_comandos_ui()

    # ======================================================
    # CHAT UI
    # ======================================================
    def init_chat_ui(self):
        layout = QVBoxLayout(self.chat_tab)

        self.area_mensagens = QVBoxLayout()
        container = QWidget()
        container.setLayout(self.area_mensagens)

        layout.addWidget(container, 1)

        input_layout = QHBoxLayout()

        self.input_mensagem = QLineEdit()
        self.input_mensagem.returnPressed.connect(self.enviar_mensagem)

        botao = QPushButton("Enviar")
        botao.clicked.connect(self.enviar_mensagem)

        input_layout.addWidget(self.input_mensagem)
        input_layout.addWidget(botao)

        layout.addLayout(input_layout)

    # ======================================================
    # Lógica Chat (100% delegada ao controller)
    # ======================================================
    def enviar_mensagem(self):
        texto = self.input_mensagem.text().strip()
        if not texto:
            return

        self.input_mensagem.clear()

        # 🔥 AGORA O CONTROLLER FAZ TUDO:
        resposta = ChatController.processar_mensagem(self.session_id, texto)

        # Atualiza interface após persistência
        self.carregar_mensagens_recentes()

    def carregar_mensagens_recentes(self):
        # limpa layout atual
        while self.area_mensagens.count():
            item = self.area_mensagens.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        self.carregar_historico()

    def adicionar_mensagem(self, texto, remetente):
        bubble = ChatBubble(texto, remetente)

        linha = QHBoxLayout()
        if remetente == "user":
            linha.addStretch()
            linha.addWidget(bubble)
        else:
            linha.addWidget(bubble)
            linha.addStretch()

        self.area_mensagens.addLayout(linha)

    def carregar_historico(self):
        mensagens = ChatController.listar_mensagens(self.session_id)

        for msg in mensagens:
            # msg = (id, remetente, conteudo, criado_em)
            _, remetente, conteudo, _ = msg
            self.adicionar_mensagem(conteudo, remetente)

    # ======================================================
    # GERENCIADOR DE COMANDOS
    # ======================================================
    def init_comandos_ui(self):
        layout = QVBoxLayout(self.comandos_tab)

        group_cmd = QGroupBox("Gerenciador de Comandos")
        group_layout = QVBoxLayout(group_cmd)

        self.lista_comandos = QListWidget()
        group_layout.addWidget(self.lista_comandos)

        btn_novo_cmd = QPushButton("Novo Comando")
        btn_novo_cmd.clicked.connect(self.abrir_dialog_comando)
        group_layout.addWidget(btn_novo_cmd)

        layout.addWidget(group_cmd)

        self.atualizar_lista_comandos()

    def atualizar_lista_comandos(self):
        self.lista_comandos.clear()

        comandos = ComandoController.listar_comandos()

        for cmd in comandos:
            # cmd = (id, nome, ativo)
            _, nome, ativo = cmd
            status = "Ativo" if ativo else "Arquivado"
            self.lista_comandos.addItem(f"{nome} - {status}")

    def abrir_dialog_comando(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Novo Comando")

        layout = QFormLayout(dialog)

        nome_input = QLineEdit()
        desc_input = QLineEdit()

        layout.addRow("Nome:", nome_input)
        layout.addRow("Descrição:", desc_input)

        btn_salvar = QPushButton("Salvar")
        layout.addWidget(btn_salvar)

        def salvar():
            nome = nome_input.text().strip()
            desc = desc_input.text().strip()

            if nome:
                ComandoController.criar_comando(nome, desc)
                self.atualizar_lista_comandos()
                dialog.accept()

        btn_salvar.clicked.connect(salvar)
        dialog.exec_()
