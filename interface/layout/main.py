from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


def build_main_area(window):
    main = QFrame()
    main.setObjectName("main")

    main_v = QVBoxLayout(main)
    main_v.setContentsMargins(12, 12, 12, 12)

    window.main_header = QLabel("Nome do atalho atual")
    window.main_header.setObjectName("mainHeader")
    window.main_header.setFont(QFont("", 14, QFont.Bold))
    main_v.addWidget(window.main_header)

    window.content_container = QWidget()
    window.content_layout = QVBoxLayout(window.content_container)
    window.content_layout.setContentsMargins(0, 0, 0, 0)

    window.placeholder_label = QLabel("Área principal — módulos irão aqui.")
    window.placeholder_label.setWordWrap(True)
    window.placeholder_label.setFont(QFont("", 12))
    window.content_layout.addWidget(window.placeholder_label)

    main_v.addWidget(window.content_container)
    main_v.addStretch()

    window.main = main
    return main
