from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


SECTIONS = [
    (
        "Seção mestre",
        [("chat", "Chat Mestre", "chat"), ("dashboard", "Painel (Dashboard)", "dashboard")],
    ),
    ("Fluxos", [("kanbans", "Kanban", "kanban"), ("library", "Biblioteca", "folder")]),
    ("Agentes", [("agents_monitor", "Agentes", "monitor")]),
]


def build_sidebar(window, icon_button_cls, nav_section_cls):
    navbar = QFrame()
    navbar.setObjectName("navbar")
    navbar.setFixedWidth(300)

    nav_v = QVBoxLayout(navbar)
    nav_v.setContentsMargins(8, 8, 8, 8)
    nav_v.setSpacing(10)

    window.profile_widget = window._create_profile_widget()
    nav_v.addWidget(window.profile_widget)

    icons_frame = QFrame()
    icons_layout = QVBoxLayout(icons_frame)
    icons_layout.setContentsMargins(0, 0, 0, 0)
    icons_layout.setSpacing(4)

    row_icons = QHBoxLayout()
    row_icons.setSpacing(16)

    window.icon_palette = icon_button_cls("brush", size=34)
    window.icon_palette.clicked.connect(window._open_personalizacao)

    window.icon_gear = icon_button_cls("gear", size=34)
    window.icon_gear.clicked.connect(window._abrir_configuracoes)

    row_icons.addWidget(window.icon_palette, alignment=Qt.AlignCenter)
    row_icons.addWidget(window.icon_gear, alignment=Qt.AlignCenter)
    icons_layout.addLayout(row_icons)

    row_labels = QHBoxLayout()
    row_labels.setSpacing(16)
    lbl_palette = QLabel("Personalização")
    lbl_palette.setAlignment(Qt.AlignCenter)
    lbl_gear = QLabel("Configurações")
    lbl_gear.setAlignment(Qt.AlignCenter)
    row_labels.addWidget(lbl_palette)
    row_labels.addWidget(lbl_gear)
    icons_layout.addLayout(row_labels)

    nav_v.addWidget(icons_frame)

    window.scroll = QScrollArea()
    window.scroll.setWidgetResizable(True)
    window.scroll_content = QWidget()
    window.scroll_content.setObjectName("navContent")
    window.scroll.setWidget(window.scroll_content)

    window.nav_layout = QVBoxLayout(window.scroll_content)
    window.nav_layout.setContentsMargins(0, 0, 0, 0)
    window.nav_layout.setSpacing(6)
    nav_v.addWidget(window.scroll, 1)

    window._nav_sections = []
    for sec_title, items in SECTIONS:
        sec = nav_section_cls(sec_title, parent=window.scroll_content)
        for key, label, icon in items:
            sec.add_shortcut(key, label, icon)
        window.nav_layout.addWidget(sec)
        window._nav_sections.append(sec)

    window.nav_layout.addStretch()
    window.navbar = navbar
    return navbar
