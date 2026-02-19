# interface/janelas/painel_central.py

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont


# ==========================================
# CARD DE MÉTRICA
# ==========================================
class MetricCard(QFrame):
    def __init__(self, titulo: str, valor: str):
        super().__init__()

        self.setObjectName("metricCard")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.titulo = QLabel(titulo)
        self.titulo.setFont(QFont("Arial", 10))
        self.titulo.setAlignment(Qt.AlignCenter)

        self.valor = QLabel(valor)
        self.valor.setFont(QFont("Arial", 18))
        self.valor.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.titulo)
        layout.addWidget(self.valor)

        self.setStyleSheet(
            """
            QFrame#metricCard {
                border-radius: 12px;
                padding: 15px;
            }
            """
        )

    def atualizar_valor(self, novo_valor: str):
        self.valor.setText(novo_valor)


# ==========================================
# DASHBOARD PRINCIPAL
# ==========================================
class MainWidget(QWidget):
    def __init__(self, dados_usuario=None):
        super().__init__()

        self.dados_usuario = dados_usuario or {}
        self.nome_usuario = self.dados_usuario.get("nome", "Usuário")

        self.init_ui()
        self.iniciar_relogio()

    # ==========================================
    # UI
    # ==========================================
    def init_ui(self):

        self.layout_principal = QVBoxLayout()
        self.layout_principal.setContentsMargins(20, 20, 20, 20)
        self.layout_principal.setSpacing(20)
        self.setLayout(self.layout_principal)

        # Título
        titulo = QLabel(f"Dashboard - Bem-vindo, {self.nome_usuario}")
        titulo.setFont(QFont("Arial", 16))
        titulo.setAlignment(Qt.AlignLeft)

        self.layout_principal.addWidget(titulo)

        # Linha de métricas
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)

        self.card_tarefas = MetricCard("Tarefas Ativas", "0")
        self.card_agentes = MetricCard("Agentes Rodando", "0")
        self.card_missoes = MetricCard("Missões Concluídas", "0")

        metrics_layout.addWidget(self.card_tarefas)
        metrics_layout.addWidget(self.card_agentes)
        metrics_layout.addWidget(self.card_missoes)

        self.layout_principal.addLayout(metrics_layout)

        # Área inferior
        area_inferior = QHBoxLayout()
        area_inferior.setSpacing(20)

        # Status do sistema
        self.card_status = MetricCard("Status do Sistema", "Online")
        self.card_relogio = MetricCard("Horário Atual", "--:--:--")

        area_inferior.addWidget(self.card_status)
        area_inferior.addWidget(self.card_relogio)

        self.layout_principal.addLayout(area_inferior)

        # Botão de atualização manual (placeholder)
        self.btn_refresh = QPushButton("Atualizar Métricas")
        self.btn_refresh.clicked.connect(self.atualizar_metricas_mock)

        self.layout_principal.addWidget(self.btn_refresh)

        # Valores mock iniciais
        self.atualizar_metricas_mock()

    # ==========================================
    # Lógica (temporária/mock)
    # ==========================================
    def atualizar_metricas_mock(self):
        """
        Placeholder até conectar com banco/agentes reais
        """
        import random

        self.card_tarefas.atualizar_valor(str(random.randint(3, 12)))
        self.card_agentes.atualizar_valor(str(random.randint(1, 5)))
        self.card_missoes.atualizar_valor(str(random.randint(10, 50)))

    def iniciar_relogio(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_relogio)
        self.timer.start(1000)

    def atualizar_relogio(self):
        hora_atual = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        self.card_relogio.atualizar_valor(hora_atual)
