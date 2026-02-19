from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy


def build_header(window):
    header = QFrame()
    header.setObjectName("header")

    header_h = QHBoxLayout(header)
    header_h.setContentsMargins(6, 6, 6, 6)
    header_h.setSpacing(8)

    window.btn_toggle_nav = QPushButton("≡")
    window.btn_toggle_nav.setFixedSize(36, 28)
    window.btn_toggle_nav.clicked.connect(window.toggle_navbar)
    header_h.addWidget(window.btn_toggle_nav)

    window.titulo = QLabel("DevHive")
    window.titulo.setObjectName("titulo")
    window.titulo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    window.titulo.setAlignment(Qt.AlignCenter)
    window.titulo.setFont(QFont("", 16, QFont.Bold))
    header_h.addWidget(window.titulo, 1)

    window.btn_min = QPushButton("—")
    window.btn_min.setFixedSize(34, 24)
    window.btn_min.clicked.connect(window.showMinimized)

    window.btn_max = QPushButton("▢")
    window.btn_max.setFixedSize(30, 30)
    window.btn_max.clicked.connect(window._toggle_max_restore)

    window.btn_close = QPushButton("✕")
    window.btn_close.setFixedSize(34, 24)
    window.btn_close.clicked.connect(window.close)

    window.btn_min.setObjectName("winMin")
    window.btn_max.setObjectName("winMax")
    window.btn_close.setObjectName("winClose")

    header_h.addWidget(window.btn_min)
    header_h.addWidget(window.btn_max)
    header_h.addWidget(window.btn_close)

    window.header = header
    return header
