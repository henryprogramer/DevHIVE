# interface/objeto/coluna_kanban.py
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSizePolicy, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from banco.controles.kanban.controle_card import ControleCardKanban
from banco.controles.kanban.controle_coluna import ControleColunaKanban
from interface.objeto.card_kanban import CardKanbanWidget


class ColunaKanbanWidget(QFrame):
    """Widget que representa uma coluna do Kanban.

    Parâmetros:
    - coluna_id: id da coluna no DB
    - titulo: título exibido
    - parent: widget pai
    - compact: se True renderiza versão compacta (para o quadro principal)
    - controle_card: instância de ControleCardKanban (opcional)
    - controle_coluna: instância de ControleColunaKanban (opcional)
    """

    def __init__(self, coluna_id=None, titulo="Nova Coluna", parent=None, compact=True,
                 controle_card=None, controle_coluna=None):
        super().__init__(parent)
        self.setObjectName("kanbanColumn")
        self.coluna_id = coluna_id
        self.titulo = titulo
        self.compact = compact

        # injeção de dependência: preferir o controle passado
        self.controle_card = controle_card if controle_card is not None else ControleCardKanban()

        # injeção / descoberta do controle de colunas
        if controle_coluna is not None:
            self.controle_coluna = controle_coluna
        else:
            # tenta achar no parent (QuadroKanbanWindow) ou cria um novo
            p = parent
            found = None
            while p:
                if hasattr(p, "controle_coluna") and getattr(p, "controle_coluna"):
                    found = getattr(p, "controle_coluna")
                    break
                try:
                    p = p.parent()
                except Exception:
                    p = None
            self.controle_coluna = found if found is not None else ControleColunaKanban()

        # callback opcional (Quadro injeta para abrir dialog)
        self.clicked_callback = None

        # estilos
        self.setStyleSheet("""
            QFrame#kanbanColumn { background: rgba(255,255,255,0.04); border-radius:8px; border: 1px solid rgba(255,255,255,0.14); }
            QLabel#colTitle { font-weight: bold; padding:6px; }
            QPushButton { background: rgba(255,255,255,0.08); border: none; border-radius: 4px; }
            QPushButton:hover { background: rgba(255,255,255,0.18); }
        """)

        # Largura/control de compact vs expanded
        if self.compact:
            self.setMinimumWidth(260)
            self.setMaximumWidth(400)
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        else:
            self.setMinimumWidth(360)
            self.setMaximumWidth(400)
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)

        header = QHBoxLayout()
        self.lbl_title = QLabel(self.titulo)
        self.lbl_title.setObjectName('colTitle')
        header.addWidget(self.lbl_title)
        header.addStretch()

        # 👁 VIEW
        btn_view = QPushButton("👁")
        btn_view.setFixedSize(26, 26)
        btn_view.setCursor(Qt.PointingHandCursor)
        btn_view.clicked.connect(self._on_view_column)
        header.addWidget(btn_view)

        # ✏ EDIT
        btn_edit = QPushButton("✏")
        btn_edit.setFixedSize(26, 26)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.clicked.connect(self._on_edit_column)
        header.addWidget(btn_edit)

        # 🗑 DELETE
        btn_delete = QPushButton("🗑")
        btn_delete.setFixedSize(26, 26)
        btn_delete.setCursor(Qt.PointingHandCursor)
        # conecta explicitamente ao handler que existe nesta classe
        btn_delete.clicked.connect(self._on_delete_column)
        header.addWidget(btn_delete)

        # ➕ ADD CARD
        btn_add = QPushButton("+")
        btn_add.setFixedSize(28, 28)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._on_add_card)
        header.addWidget(btn_add)

        self.main_layout.addLayout(header)

        # area de cards (scroll vertical)
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards_scroll.setFrameShape(QScrollArea.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setSpacing(8)
        self.cards_container.setLayout(self.cards_layout)

        self.cards_scroll.setWidget(self.cards_container)
        self.main_layout.addWidget(self.cards_scroll)

        # placeholder quando não há cards
        self._empty_label = QLabel('(Nenhum card)')

        # carregar cards iniciais (tenta, não falha se der exceção)
        try:
            self.load_cards()
        except Exception as e:
            print("ColunaKanbanWidget.load_cards erro:", e)

    # ---------------------------------
    # UI e interações
    # ---------------------------------
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.clicked_callback:
            try:
                self.clicked_callback(self)
            except Exception:
                pass
        return super().mousePressEvent(ev)

    def _on_add_card(self):
        titulo, ok = QInputDialog.getText(self, 'Novo Card', 'Título:')
        if not ok or not titulo.strip():
            return
        try:
            created = self.controle_card.criar_card(coluna_id=self.coluna_id, titulo=titulo.strip())
            QMessageBox.information(self, 'Card', 'Card criado.')
            self.load_cards()
            # notifica parent (quadro) para reordenar se necessário
            parent = self.parent()
            if parent and hasattr(parent, 'refresh'):
                try:
                    parent.refresh()
                except Exception:
                    pass
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f'Não foi possível criar card: {e}')

    def clear_cards_ui(self):
        for i in reversed(range(self.cards_layout.count())):
            w = self.cards_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

    def load_cards(self):
        self.clear_cards_ui()
        cards = []
        try:
            if self.controle_card and self.coluna_id is not None:
                cards = self.controle_card.listar_cards(coluna_id=self.coluna_id, pai_id=None)
        except Exception as e:
            print('Erro ao listar cards na coluna:', e)
            cards = []

        if not cards:
            self.cards_layout.addWidget(self._empty_label)
            return

        for c in cards:
            try:
                card_widget = CardKanbanWidget(card_id=c.get('id'), titulo=c.get('titulo'),
                                               coluna_id=self.coluna_id, parent_coluna=self)
                card_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                self.cards_layout.addWidget(card_widget)
            except Exception as e:
                print('Erro criando CardKanbanWidget:', e)

    # alias
    def refresh(self):
        self.load_cards()

    def refresh_cards(self):
        self.refresh()

    def remove_card_widget(self, card_widget):
        try:
            self.cards_layout.removeWidget(card_widget)
            card_widget.deleteLater()
        except Exception:
            pass

    # ---- handlers ----
    def _on_view_column(self):
        if self.clicked_callback:
            try:
                self.clicked_callback(self)
            except Exception:
                pass

    def _on_edit_column(self):
        novo_titulo, ok = QInputDialog.getText(self, "Editar Coluna", "Novo título:", text=self.titulo)
        if not ok or not novo_titulo.strip():
            return
        try:
            sucesso = self.controle_coluna.editar_coluna(self.coluna_id, novo_titulo.strip())
            if sucesso:
                self.titulo = novo_titulo.strip()
                self.lbl_title.setText(self.titulo)
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível editar a coluna.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def _on_delete_column(self):
        """Handler de exclusão — usa controle de colunas (injeção) e mostra confirmação."""
        # verifica cards presentes
        try:
            num_cards = 0
            if hasattr(self, "controle_coluna") and self.controle_coluna:
                # se controle_coluna implementou contar_cards_na_coluna, usa
                try:
                    num_cards = self.controle_coluna.contar_cards_na_coluna(self.coluna_id)
                except AttributeError:
                    # fallback direto
                    from banco.database import conectar
                    conn = conectar()
                    cur = conn.cursor()
                    try:
                        cur.execute("SELECT COUNT(*) FROM kanban_cards WHERE coluna_id = ?", (self.coluna_id,))
                        num_cards = int(cur.fetchone()[0])
                    finally:
                        conn.close()
        except Exception as e:
            print("Erro ao verificar cards antes de excluir coluna:", e)
            num_cards = 0

        if num_cards > 0:
            resposta = QMessageBox.question(
                self,
                "Excluir Coluna (com cards)",
                f"A coluna '{self.titulo}' tem {num_cards} card(s). Deseja excluir a coluna e todos os cards (remoção em cascata)?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if resposta != QMessageBox.Yes:
                return
        else:
            resposta = QMessageBox.question(
                self,
                "Excluir Coluna",
                f"Deseja realmente excluir '{self.titulo}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if resposta != QMessageBox.Yes:
                return

        # tenta deletar agora
        try:
            sucesso = self.controle_coluna.deletar_coluna(self.coluna_id)
            if sucesso:
                parent = self.parent()
                if parent and hasattr(parent, "load_columns"):
                    parent.load_columns()
                else:
                    # fallback visual
                    try:
                        self.setParent(None)
                        self.deleteLater()
                    except Exception:
                        pass
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível excluir a coluna.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao excluir coluna: {e}")
