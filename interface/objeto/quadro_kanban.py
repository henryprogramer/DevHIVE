# interface/objeto/quadro_kanban.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QInputDialog, QMessageBox,
    QPushButton, QHBoxLayout, QScrollArea, QFrame, QSizePolicy,
    QApplication, QDialog
)
from PyQt5.QtCore import Qt, QEvent, QPoint
from PyQt5.QtGui import QPixmap, QCursor

from banco.controles.kanban.controle_kanban import ControleKanban
from banco.controles.kanban.controle_coluna import ControleColunaKanban
from banco.controles.kanban.controle_card import ControleCardKanban

from interface.objeto.coluna_kanban import ColunaKanbanWidget


class QuadroKanbanWindow(QWidget):

    def __init__(self, quadro_id=None, nome_quadro=None, controle_coluna=None, controle_card=None, parent=None):
        super().__init__(parent)
        self.quadro_id = quadro_id
        self.controle_coluna = controle_coluna or ControleColunaKanban()
        self.controle_card = controle_card or ControleCardKanban()

        # força mínima de altura global da janela/quadro
        self.setMinimumHeight(900)

        self._coluna_widgets = []

        self.nome_quadro = nome_quadro or self.buscar_nome_quadro()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(10)

        # HEADER
        header_layout = QHBoxLayout()
        self.btn_voltar = QPushButton("⬅ Voltar")
        self.btn_voltar.setFixedHeight(40)
        self.btn_voltar.clicked.connect(self.voltar_para_painel)

        self.header = QLabel(f"Quadro Kanban — {self.nome_quadro}")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("font-weight: bold; font-size: 20px;")

        header_layout.addWidget(self.btn_voltar)
        header_layout.addWidget(self.header, 1)
        self.layout.addLayout(header_layout)

        # ==============================
        # ÁREA DE COLUNAS (FORÇADA PARA 900px)
        # ==============================
        self.columns_scroll = QScrollArea()
        self.columns_scroll.setWidgetResizable(True)
        self.columns_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.columns_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.columns_scroll.setFrameShape(QFrame.NoFrame)

        # Forçar altura mínima de exibição das colunas para 900px
        self.columns_scroll.setMinimumHeight(900)
        self.columns_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.columns_container = QWidget()
        self.columns_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Forçar altura mínima interna também
        self.columns_container.setMinimumHeight(900)

        self.columns_layout = QHBoxLayout(self.columns_container)
        self.columns_layout.setContentsMargins(10, 10, 10, 10)
        self.columns_layout.setSpacing(16)

        self.columns_scroll.setWidget(self.columns_container)

        # Colocar stretch maior (prioridade de expansão vertical)
        # o segundo argumento (10) fornece um peso alto no layout vertical
        self.layout.addWidget(self.columns_scroll, 10)

        # placeholder
        self.add_column_placeholder = self._create_add_column_placeholder()

        # carregar colunas
        self.load_columns()

        # garantir que o widget principal não fique abaixo do mínimo
        self.setMinimumHeight(900)

    # ==============================
    # MÉTODOS
    # ==============================

    def buscar_nome_quadro(self):
        return f"Quadro {self.quadro_id}" if self.quadro_id else "Quadro"

    def voltar_para_painel(self):
        root = self.parent()
        while root:
            if hasattr(root, "clear_content_container"):
                root.clear_content_container()
                root.load_shortcut_module("kanbans")
                return
            root = root.parent()
    # ==============================
    # MÉTODOS ESTÁTICOS DE DIÁLOGO
    # ==============================

    @staticmethod
    def criar_novo_quadro(parent=None):
        nome, ok = QInputDialog.getText(parent, "Novo Quadro", "Nome do quadro:")
        if ok and nome.strip():
            return nome.strip()
        return None


    @staticmethod
    def editar_nome_quadro(parent=None, nome_atual=""):
        nome, ok = QInputDialog.getText(
            parent,
            "Editar Quadro",
            "Novo nome:",
            text=nome_atual
        )
        if ok and nome.strip():
            return nome.strip()
        return None


    @staticmethod
    def confirmar_exclusao(parent=None, nome=""):
        resposta = QMessageBox.question(
            parent,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o quadro '{nome}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return resposta == QMessageBox.Yes

    def _create_add_column_placeholder(self):
        placeholder = QFrame()
        placeholder.setMinimumWidth(260)
        placeholder.setMaximumWidth(260)
        placeholder.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        placeholder.setStyleSheet("""
            QFrame { 
                background-color: rgba(58, 58, 58, 180); 
                border: 1px solid grey;
                border-radius: 8px;
            }
            QFrame:hover { 
                background-color: rgba(128, 128, 128, 200); 
            }
        """)


        v = QVBoxLayout(placeholder)
        v.addStretch()
        plus = QLabel("+")
        plus.setAlignment(Qt.AlignCenter)
        plus.setStyleSheet("border: none; background-color: transparent; font-size: 40px;")
        v.addWidget(plus)
        v.addStretch()

        def _mouse_press(ev):
            if ev.button() == Qt.LeftButton:
                self._on_add_column_clicked()
        placeholder.mousePressEvent = _mouse_press

        return placeholder

    def load_columns(self):
        # limpa o layout de colunas
        while self.columns_layout.count():
            item = self.columns_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        self._coluna_widgets = []

        colunas = []
        try:
            colunas = self.controle_coluna.listar_colunas(self.quadro_id) or []
        except Exception as e:
            print("Erro ao listar colunas:", e)

        for coluna in colunas:
            widget_coluna = ColunaKanbanWidget(
                coluna_id=coluna.get("id"),
                titulo=coluna.get("titulo"),
                parent=self,
                compact=True,
                controle_card=self.controle_card,
                controle_coluna=self.controle_coluna   # <-- adicionado
            )


            widget_coluna.setMinimumWidth(260)
            widget_coluna.setMaximumWidth(400)
            widget_coluna.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

            # garantir que a coluna carregue seus cards
            if hasattr(widget_coluna, "load_cards"):
                try:
                    widget_coluna.load_cards()
                except Exception:
                    pass

            self.columns_layout.addWidget(widget_coluna)
            self._coluna_widgets.append(widget_coluna)

        # adicionar placeholder e stretch
        self.columns_layout.addWidget(self.add_column_placeholder)
        self.columns_layout.addStretch(1)

    def _on_add_column_clicked(self):
        titulo, ok = QInputDialog.getText(self, "Nova Coluna", "Título da coluna:")
        if not ok:
            return
        titulo = titulo.strip() or "Nova Coluna"

        created = self.controle_coluna.criar_coluna(self.quadro_id, titulo)
        if not created:
            QMessageBox.warning(self, "Erro", "Não foi possível criar a coluna.")
            return

        # recarrega colunas (garante que nova coluna apareça)
        self.load_columns()

    # ==============================
    # RESIZE: mantem mínimo de 900px
    # ==============================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            total_height = self.height()
            header_height = 80
            nova_altura = max(900, total_height - header_height)

            self.columns_scroll.setMinimumHeight(nova_altura)
            self.columns_container.setMinimumHeight(nova_altura)
            # reforça altura mínima do próprio widget
            self.setMinimumHeight(900)
        except Exception:
            pass
