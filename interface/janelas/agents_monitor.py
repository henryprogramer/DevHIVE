from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget


class StatusCard(QFrame):
    def __init__(self, titulo: str, status: str, detalhe: str):
        super().__init__()
        self.setObjectName("agentStatusCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("", 11, QFont.Bold))
        layout.addWidget(lbl_titulo)

        lbl_status = QLabel(f"Status: {status}")
        lbl_status.setFont(QFont("", 10))
        layout.addWidget(lbl_status)

        lbl_detalhe = QLabel(detalhe)
        lbl_detalhe.setWordWrap(True)
        layout.addWidget(lbl_detalhe)

        self.setStyleSheet(
            """
            QFrame#agentStatusCard {
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.04);
            }
            """
        )


class MainWidget(QWidget):
    def __init__(self, dados_usuario=None):
        super().__init__()
        self.dados_usuario = dados_usuario or {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        titulo = QLabel("Agentes")
        titulo.setFont(QFont("", 16, QFont.Bold))
        root.addWidget(titulo)

        subtitulo = QLabel("Resumo simples dos modulos de agente encontrados no projeto.")
        subtitulo.setWordWrap(True)
        subtitulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        root.addWidget(subtitulo)

        grid = QGridLayout()
        grid.setSpacing(12)
        root.addLayout(grid)

        modulos = self._coletar_status_agentes()
        if not modulos:
            aviso = QLabel("Nenhum modulo de agente encontrado.")
            aviso.setWordWrap(True)
            root.addWidget(aviso)
            return

        for i, item in enumerate(modulos):
            card = StatusCard(item["nome"], item["status"], item["detalhe"])
            row = i // 2
            col = i % 2
            grid.addWidget(card, row, col)

        root.addStretch(1)

    def _coletar_status_agentes(self):
        base_dir = Path(__file__).resolve().parents[2]
        agentes_dir = base_dir / "agentes"
        if not agentes_dir.exists():
            return []

        itens = []
        for arquivo in sorted(agentes_dir.glob("agente_*.py")):
            nome = arquivo.stem.replace("_", " ").title()
            size = arquivo.stat().st_size
            status = "Pronto" if size > 0 else "Placeholder"
            detalhe = f"Arquivo: {arquivo.name} ({size} bytes)"
            itens.append(
                {
                    "nome": nome,
                    "status": status,
                    "detalhe": detalhe,
                }
            )

        return itens
