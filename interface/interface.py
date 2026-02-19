import traceback
from typing import Dict, Optional

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from banco.controles.tema.controle_tema import ControleTema
from interface.layout.header import build_header
from interface.layout.main import build_main_area
from interface.layout.sidebar import build_sidebar
from interface.window.constants import PAGE_MAP
from interface.window.navigation_mixin import NavigationMixin
from interface.window.profile_mixin import ProfileMixin
from interface.window.theme_mixin import ThemeMixin
from interface.window.widgets import NavSection, VectorIconButton
from interface.window.window_mixin import WindowMixin


class InterfaceWindow(ProfileMixin, ThemeMixin, NavigationMixin, WindowMixin, QMainWindow):
    def __init__(self, dados_usuario: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.dados_usuario = dados_usuario or {}

        try:
            self.theme_controller = ControleTema()
        except Exception:
            traceback.print_exc()
            self.theme_controller = None

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.tema_atual = "dark"
        self.cor_fundo = None
        self.cor_destaque = None
        self.imagem_fundo = None
        self._tmp_image_path = None
        self.imagem_opacity = 0.8
        self._drag_pos = None
        self._is_dragging = False
        self.page_modules_map: Dict[str, str] = dict(PAGE_MAP)
        self.neko = None
        self._profile_card = None
        self._compact_profile_container = None
        self.setWindowTitle("DevHive")
        self.showMaximized()

        self._theme_state = {
            "scope": "Global",
            "theme_mode": "dark",
            "cor_fundo": None,
            "cor_destaque": None,
            "imagem_fundo": None,
            "imagem_opacity": self.imagem_opacity,
        }

        self.init_ui()

        try:
            if self.theme_controller:
                active = self.theme_controller.get_active()
                if active:
                    self._apply_theme_record_to_state(active)
        except Exception:
            traceback.print_exc()

        if hasattr(self, "combo_tema"):
            self.combo_tema.setCurrentText(self.tema_atual.capitalize())
        self.aplicar_tema_padrao()
        QTimer.singleShot(120, self._try_init_neko)

    def init_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_v = QVBoxLayout(central)
        root_v.setContentsMargins(8, 8, 8, 8)

        root_v.addWidget(build_header(self))

        center = QFrame()
        center.setObjectName("centerFrame")
        center_h = QHBoxLayout(center)
        center_h.setContentsMargins(0, 0, 0, 0)

        center_h.addWidget(build_sidebar(self, VectorIconButton, NavSection))
        center_h.addWidget(build_main_area(self), 1)

        self.criar_painel_customizacao()
        center_h.addWidget(self.painel)

        root_v.addWidget(center, 1)

        if self._nav_sections and self._nav_sections[0].items:
            first = self._nav_sections[0].items[0]
            first.selected = True
            first.update()
            self.handle_nav_activation(first.key, first.label)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = InterfaceWindow(dados_usuario={})
    w.show()
    sys.exit(app.exec_())
