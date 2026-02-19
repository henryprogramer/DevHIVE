# interface/widgets_neko.py
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont

class NekoOrb(QWidget):
    """
    Bola flutuante simples — minimal e robusto.
    Deve ser instanciada com parent=InterfaceWindow preferencialmente.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 110)
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        self.lbl = QLabel("neko")
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(self.lbl)
        # animação simples de brilho (muda cor a cada 500ms)
        self._color_phase = 0
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._next_phase)
        self._timer.start()

    def _next_phase(self):
        self._color_phase = (self._color_phase + 1) % 6
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)
        # cor cíclica
        colors = [
            QColor(58, 140, 255, 220),
            QColor(80, 200, 120, 220),
            QColor(255, 190, 60, 220),
            QColor(220, 100, 200, 220),
            QColor(160, 120, 255, 220),
            QColor(255, 100, 100, 220),
        ]
        c = colors[self._color_phase]
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.drawEllipse(r)
        p.end()
