from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGridLayout, QFrame, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt

# Importação dos controles
from banco.controles.kanban.controle_kanban import ControleKanban
from banco.controles.kanban.controle_coluna import ControleColunaKanban
from banco.controles.kanban.controle_card import ControleCardKanban
from interface.objeto.quadro_kanban import QuadroKanbanWindow

class PainelKanban(QWidget):
    def __init__(self, dados_usuario=None):
        super().__init__()

        self.dados_usuario = dados_usuario or {}
        self.user_id = self.dados_usuario.get("id")

        # Controles que acessam o Banco de Dados
        self.controle_kanban = ControleKanban()
        self.controle_coluna = ControleColunaKanban()
        self.controle_card = ControleCardKanban()

        self.setWindowTitle("Meus Quadros Kanban")
        self.resize(900, 700)

        # Layout Principal
        self.layout_principal = QVBoxLayout(self)

        # ==========================================
        # ÁREA DE GRADE (SCROLLABLE)
        # ==========================================
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        
        self.container_grade = QWidget()
        self.grid_layout = QGridLayout(self.container_grade)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.grid_layout.setSpacing(25) 
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        
        self.scroll.setWidget(self.container_grade)
        self.layout_principal.addWidget(self.scroll)

        # ==========================================
        # BOTÃO NOVO QUADRO
        # ==========================================
        self.btn_novo_quadro = QPushButton("➕ Criar Novo Quadro")
        self.btn_novo_quadro.setObjectName("btnNovoQuadro")
        self.btn_novo_quadro.setFixedHeight(45)
        self.btn_novo_quadro.setCursor(Qt.PointingHandCursor)
        self.layout_principal.addWidget(self.btn_novo_quadro)

        # Conexões
        self.btn_novo_quadro.clicked.connect(self.acao_novo_quadro)

        self.carregar_quadros()

    def limpar_grade(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def carregar_quadros(self):
        """Busca no banco e exibe na grade."""
        self.limpar_grade()

        try:
            quadros = self.controle_kanban.listar_quadros(self.user_id)
        except Exception:
            quadros = []

        if not quadros:
            return

        colunas_max = 3
        for index, quadro in enumerate(quadros):
            nome = quadro.get("nome", "Sem nome")
            qid = quadro.get("id")

            card = self.criar_card_quadro(nome, qid)
            
            linha = index // colunas_max
            coluna = index % colunas_max
            self.grid_layout.addWidget(card, linha, coluna)

    def criar_card_quadro(self, nome, qid):
        """Cria um widget visual (Card) com Editar, Excluir e Abrir."""
        card = QFrame()
        card.setObjectName("kanbanBoardCard")
        card.setFixedSize(220, 180) # Aumentado para acomodar os novos botões

        layout_card = QVBoxLayout(card)
        
        # Título do Quadro
        label_nome = QLabel(nome)
        label_nome.setAlignment(Qt.AlignCenter)
        label_nome.setWordWrap(True)
        label_nome.setStyleSheet("font-size: 18px; font-weight: bold; border: none; background: transparent;")
        layout_card.addWidget(label_nome)

        # Layout para os botões de ação (Editar e Excluir)
        layout_acoes = QHBoxLayout()
        
        btn_editar = QPushButton("✏️")
        btn_editar.setToolTip("Editar nome")
        btn_editar.setFixedSize(40, 30)
        btn_editar.setCursor(Qt.PointingHandCursor)
        btn_editar.setStyleSheet("QPushButton { border: 1px solid #ccc; border-radius: 4px; background: #3498DB; color: #fff;} QPushButton:hover { background: #eee; border: 1px solid #3498DB; color: #3498DB;}")
        btn_editar.clicked.connect(lambda: self.acao_editar_quadro(qid, nome))

        btn_excluir = QPushButton("🗑️")
        btn_excluir.setToolTip("Excluir quadro")
        btn_excluir.setFixedSize(40, 30)
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setStyleSheet("QPushButton { border: 1px solid #ccc; border-radius: 4px; background: #E74C3C; color: #fff;} QPushButton:hover { background: #fee; color: red; border: 1px solid red; }")
        btn_excluir.clicked.connect(lambda: self.acao_excluir_quadro(qid, nome))

        layout_acoes.addWidget(btn_editar)
        layout_acoes.addWidget(btn_excluir)
        layout_card.addLayout(layout_acoes)

        # Botão Abrir
        btn_abrir = QPushButton("Abrir")
        btn_abrir.setObjectName("btnAbrirQuadro")
        btn_abrir.setCursor(Qt.PointingHandCursor)
        btn_abrir.setFixedHeight(35)
        btn_abrir.clicked.connect(lambda ch, q=qid, n=nome: self.abrir_quadro_por_id(q, n))
        layout_card.addWidget(btn_abrir)

        return card

    # --- FUNÇÕES DE AÇÃO ---

    def acao_novo_quadro(self):
        nome = QuadroKanbanWindow.criar_novo_quadro(self)
        if nome:
            self.controle_kanban.criar_quadro(user_id=self.user_id, nome=nome)
            self.carregar_quadros()

    def acao_editar_quadro(self, qid, nome_atual):
        novo_nome = QuadroKanbanWindow.editar_nome_quadro(self, nome_atual)
        if novo_nome:
            if self.controle_kanban.editar_quadro(qid, novo_nome):
                self.carregar_quadros()

    def acao_excluir_quadro(self, qid, nome):
        if QuadroKanbanWindow.confirmar_exclusao(self, nome):
            if self.controle_kanban.deletar_quadro(qid):
                self.carregar_quadros()

    def abrir_quadro_por_id(self, quadro_id, nome_quadro):
        """
        Abre o quadro embutido no main da InterfaceWindow exibindo o NOME do quadro.
        Se não encontrar a Interface principal, abre como janela (fallback).
        """

        # =========================
        # 1) PROCURAR A INTERFACE PRINCIPAL
        # =========================
        root = self
        interface_candidate = None

        while root is not None:
            if hasattr(root, "content_layout") and hasattr(root, "clear_content_container"):
                interface_candidate = root
                break
            root = root.parent()

        # =========================
        # 2) ABRIR EMBUTIDO NO MAIN
        # =========================
        if interface_candidate is not None:
            try:
                interface_candidate.clear_content_container()

                quadro_widget = QuadroKanbanWindow(
                    quadro_id=quadro_id,
                    nome_quadro=nome_quadro,  # agora vem direto do card
                    controle_coluna=self.controle_coluna,
                    controle_card=self.controle_card,
                    parent=interface_candidate.content_container
                )

                interface_candidate.content_layout.addWidget(quadro_widget)

                try:
                    interface_candidate.main_header.setText(f"Quadro Kanban — {nome_quadro}")
                except Exception:
                    pass

                quadro_widget.show()
                return

            except Exception as e:
                print("Erro ao embutir quadro no main:", e)

        # =========================
        # 3) FALLBACK: JANELA SEPARADA
        # =========================
        try:
            self.janela_quadro = QuadroKanbanWindow(
                quadro_id=quadro_id,
                nome_quadro=nome_quadro,
                controle_coluna=self.controle_coluna,
                controle_card=self.controle_card
            )
            self.janela_quadro.setWindowFlags(Qt.Window)
            self.janela_quadro.show()

        except Exception as e:
            print(f"Erro ao abrir quadro em janela separada: {e}")
