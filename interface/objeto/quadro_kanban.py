# interface/objeto/quadro_kanban.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QInputDialog, QMessageBox,
    QPushButton, QHBoxLayout, QScrollArea, QFrame, QSizePolicy,
    QApplication
)
from PyQt5.QtCore import Qt
from banco.controles.kanban.controle_coluna import ControleColunaKanban
from banco.controles.kanban.controle_card import ControleCardKanban
from interface.objeto.coluna_kanban import ColunaKanbanWidget


class QuadroKanbanWindow(QWidget):

    def __init__(self, quadro_id=None, nome_quadro=None, controle_coluna=None, controle_card=None, parent=None):
        super().__init__(parent)
        self.quadro_id = quadro_id
        self.controle_coluna = controle_coluna or ControleColunaKanban()
        self.controle_card = controle_card or ControleCardKanban()

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

        # ÁREA DE COLUNAS
        self.columns_scroll = QScrollArea()
        self.columns_scroll.setWidgetResizable(True)
        self.columns_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.columns_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.columns_scroll.setFrameShape(QFrame.NoFrame)
        self.columns_scroll.setMinimumHeight(600)
        self.columns_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.columns_container = QWidget()
        self.columns_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.columns_container.setMinimumHeight(600)

        # layout horizontal para colunas — alinhado à esquerda para não "empurrar" o placeholder
        self.columns_layout = QHBoxLayout(self.columns_container)
        self.columns_layout.setContentsMargins(10, 10, 10, 10)
        self.columns_layout.setSpacing(16)
        self.columns_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.columns_scroll.setWidget(self.columns_container)
        self.layout.addWidget(self.columns_scroll, 1)

        # carregar colunas (o placeholder será criado dentro de load_columns)
        self.load_columns()

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

    @staticmethod
    def criar_novo_quadro(parent=None):
        nome, ok = QInputDialog.getText(parent, "Novo Quadro", "Nome do quadro:")
        if ok and nome.strip():
            return nome.strip()
        return None

    @staticmethod
    def editar_nome_quadro(parent=None, nome_atual=""):
        nome, ok = QInputDialog.getText(parent, "Editar Quadro", "Novo nome:", text=nome_atual)
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

    # ---------- novo placeholder claro e responsivo (QPushButton) ----------
    def _create_add_column_button(self):
        btn = QPushButton("+\nAdicionar coluna")
        btn.setObjectName("addColumnButton")
        btn.setFixedWidth(260)
        btn.setMinimumHeight(160)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.StrongFocus)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.16);
                border-radius: 8px;
                font-size: 18px;
                padding: 8px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.10);
            }
            QPushButton:pressed {
                background-color: rgba(255,255,255,0.16);
            }
        """)
        btn.clicked.connect(self._on_add_column_clicked)

        return btn

    def load_columns(self):
        """
        Recarrega as colunas do quadro.
        Limpa corretamente widgets e itens do layout, recria placeholder como botão visível e força redraw.
        """
        # limpa o layout de colunas (trata widgets e spacers)
        while self.columns_layout.count():
            item = self.columns_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            # spacers/itens não-widget já foram removidos pelo takeAt

        self._coluna_widgets = []

        # recria placeholder (agora botão)
        self.add_column_button = self._create_add_column_button()

        colunas = []
        try:
            colunas = self.controle_coluna.listar_colunas(self.quadro_id) or []
        except Exception as e:
            # não interrompe a UI — mostra o placeholder mesmo que a listagem falhe
            print("Erro ao listar colunas:", e)
            colunas = []

        for coluna in colunas:
            widget_coluna = ColunaKanbanWidget(
                coluna_id=coluna.get("id"),
                titulo=coluna.get("titulo"),
                parent=self,
                compact=True,
                controle_card=self.controle_card,
                controle_coluna=self.controle_coluna
            )
            widget_coluna.setMinimumWidth(260)
            widget_coluna.setMaximumWidth(400)
            widget_coluna.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

            if hasattr(widget_coluna, "load_cards"):
                try:
                    widget_coluna.load_cards()
                except Exception:
                    pass

            self.columns_layout.addWidget(widget_coluna)
            self._coluna_widgets.append(widget_coluna)

        # sempre adicionar o botão de nova coluna ao final (visível mesmo com zero colunas)
        self.columns_layout.addWidget(self.add_column_button)
        # adiciona um pequeno spacer para evitar que o botão fique colado à borda direita em janelas largas
        self.columns_layout.addStretch(1)

        # força atualização visual do container
        self.columns_container.adjustSize()
        self.columns_container.update()
        self.columns_scroll.update()
        QApplication.processEvents()

    def _on_add_column_clicked(self):
        titulo, ok = QInputDialog.getText(self, "Nova Coluna", "Título da coluna:")
        if not ok:
            return
        titulo = titulo.strip() or "Nova Coluna"

        created = self.controle_coluna.criar_coluna(self.quadro_id, titulo)
        if not created:
            QMessageBox.warning(self, "Erro", "Não foi possível criar a coluna.")
            return

        # recarrega colunas
        self.load_columns()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            total_height = self.height()
            header_height = 80
            nova_altura = max(600, total_height - header_height)
            self.columns_scroll.setMinimumHeight(nova_altura)
            self.columns_container.setMinimumHeight(nova_altura)
            self.setMinimumHeight(600)
        except Exception:
            pass
