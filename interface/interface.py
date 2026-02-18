# interface.py
# Interface principal — layout + personalização + ícones vetoriais + frameless + neon (via QGraphicsDropShadowEffect)
# Atualizado: pesquisa módulos em interface.janelas.*, aceita várias convenções de classe (MainWidget, MainPage, Painel*, etc.)
# e posicionamento robusto do NekoOrb (considera parent=centralWidget).

import os
import tempfile
import traceback
import importlib
import inspect
from math import sin, cos, pi
from typing import Optional, Dict

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QColorDialog, QFileDialog,
    QComboBox, QFrame, QMessageBox, QSlider,
    QSizePolicy, QToolButton, QGraphicsDropShadowEffect,
    QScrollArea, QApplication
)
from PyQt5.QtCore import Qt, QUrl, QEvent, QTimer, QRectF, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainterPath, QFont, QPalette

# ---------------- mapping de keys para tipos de ícone ----------------
ICON_KEY_TO_TYPE = {
    "chat": "chat",
    "dashboard": "dashboard",
    "kanbans": "kanban",
    "agents_monitor": "detective",
    "monitor": "detective",
    "palette": "brush",
    "gear": "gear",
    "user": "user",
    "folder": "folder",
    "chart": "chart",
}

# ---------------- fallback PAGE_MAP (prioriza modules dentro de interface/) ----------------
PAGE_MAP = {
    "chat": "interface.janelas.chat_ui",
    "dashboard": "interface.janelas.painel_central",
    # atualizado para a nova localização em interface/janelas
    "kanbans": "interface.janelas.painel_kanban",
    "agents_monitor": "interface.janelas.agents_monitor",  # placeholder; ajuste se criar esse módulo
}


# ---------------- VectorIconButton (vetorial, pintável) ----------------
class VectorIconButton(QToolButton):
    def __init__(self, icon_type="palette", size=36, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self._size = size
        self.icon_color = QColor(255, 255, 255)
        self.bg_color = QColor(255, 255, 255, 12)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(size + 8, size + 8)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setStyleSheet("background: transparent; border: none;")

    def set_icon_color(self, qcolor):
        if isinstance(qcolor, QColor):
            self.icon_color = qcolor
        else:
            self.icon_color = QColor(qcolor)
        self.update()

    def set_bg_color(self, qcolor):
        if isinstance(qcolor, QColor):
            self.bg_color = qcolor
        else:
            self.bg_color = QColor(qcolor)
        self.update()

    def paintEvent(self, e):
        s = self._size
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)
        p.setPen(Qt.NoPen)
        p.setBrush(self.bg_color)
        p.drawEllipse(QRectF(rect))
        p.translate(self.width() / 2.0, self.height() / 2.0)
        try:
            if self.icon_type == "palette":
                self._draw_palette(p, s)
            elif self.icon_type == "gear":
                self._draw_gear(p, s)
            elif self.icon_type == "chat":
                self._draw_chat_robot(p, s)
            elif self.icon_type == "dashboard":
                self._draw_dashboard(p, s)
            elif self.icon_type == "kanban":
                self._draw_kanban(p, s)
            elif self.icon_type == "monitor":
                self._draw_monitor(p, s)
            elif self.icon_type == "user":
                self._draw_user(p, s)
            elif self.icon_type == "folder":
                self._draw_folder(p, s)
            elif self.icon_type == "chart":
                self._draw_chart(p, s)
            elif self.icon_type == "brush":
                self._draw_brush(p, s)
            elif self.icon_type == "detective":
                self._draw_detective(p, s)
            else:
                p.setBrush(self.icon_color)
                r = s * 0.22
                p.drawEllipse(QRectF(-r/2.0, -r/2.0, r, r))
        finally:
            p.end()

    def _draw_palette(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        path = QPainterPath()
        path.addEllipse(-10, -8, 22, 16)
        p.drawPath(path)
        p.setBrush(QColor(30, 30, 30))
        p.drawEllipse(QRectF(6, -2, 6, 6))
        p.restore()

    def _draw_brush(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        p.drawRoundedRect(QRectF(-2, -10, 4, 16), 1, 1)
        path = QPainterPath()
        path.moveTo(-4, 6)
        path.lineTo(4, 6)
        path.lineTo(2, 12)
        path.lineTo(-2, 12)
        path.closeSubpath()
        p.drawPath(path)
        p.restore()

    def _draw_detective(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        p.drawRoundedRect(QRectF(-10, -8, 20, 4), 2, 2)
        p.drawRect(QRectF(-6, -10, 12, 3))
        p.drawEllipse(QRectF(-5, -4, 10, 8))
        p.drawRoundedRect(QRectF(-6, 2, 12, 8), 2, 2)
        p.restore()

    def _draw_gear(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        center_r = 6.0
        p.drawEllipse(QRectF(-center_r, -center_r, center_r * 2.0, center_r * 2.0))
        p.setBrush(QColor(20, 20, 20))
        p.drawEllipse(QRectF(-2.0, -2.0, 4.0, 4.0))
        p.restore()

    def _draw_chat_robot(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        p.drawRoundedRect(QRectF(-10, -7, 20, 14), 3, 3)
        p.setBrush(QColor(18, 18, 18))
        p.drawEllipse(QRectF(-6, -2, 3, 3))
        p.drawEllipse(QRectF(3, -2, 3, 3))
        p.setBrush(self.icon_color)
        p.drawRect(QRectF(-1.0, -12.0, 2.0, 4.0))
        p.restore()

    def _draw_dashboard(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        p.drawRoundedRect(QRectF(-10, -7, 20, 12), 2, 2)
        p.setBrush(QColor(20, 20, 20))
        p.drawRect(QRectF(-4, 6, 8, 2))
        p.restore()

    def _draw_kanban(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        cols = [(-10, -8, 6, 14), (-2, -8, 4, 14), (6, -8, 6, 14)]
        for x, y, w, h in cols:
            p.setBrush(self.icon_color)
            p.drawRoundedRect(QRectF(x, y, w, h), 1, 1)
            p.setBrush(QColor(18, 18, 18))
            p.drawRect(QRectF(x + 1, y + 1, w - 2, 3))
        p.restore()

    def _draw_monitor(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        p.drawRoundedRect(QRectF(-10, -6, 20, 12), 2, 2)
        p.setBrush(QColor(20, 20, 20))
        p.drawRect(QRectF(-4, 6, 8, 2))
        p.restore()

    def _draw_user(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        p.drawEllipse(QRectF(-6, -8, 12, 8))
        p.drawEllipse(QRectF(-4, 0, 8, 10))
        p.restore()

    def _draw_folder(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        p.drawRoundedRect(QRectF(-10, -6, 12, 8), 1, 1)
        p.drawRect(QRectF(-10, -2, 20, 10))
        p.restore()

    def _draw_chart(self, p: QPainter, s: int):
        p.save()
        scale = s / 36.0
        p.scale(scale, scale)
        p.setPen(Qt.NoPen)
        p.setBrush(self.icon_color)
        p.drawRect(QRectF(-10, -8, 4, 12))
        p.drawRect(QRectF(-4, -4, 4, 8))
        p.drawRect(QRectF(2, -1, 4, 5))
        p.restore()


# ---------------- ShortcutItem (define icon_type via key) ----------------
class ShortcutItem(QWidget):
    def __init__(self, key: str, label: str, icon_type="folder", parent=None):
        super().__init__(parent)
        self.key = key
        self.label = label
        self.icon_type = ICON_KEY_TO_TYPE.get(key, icon_type)
        self.selected = False
        self._hover_style = "background: transparent;"
        self.setMinimumHeight(48)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        self.setLayout(layout)
        self.icon_btn = VectorIconButton(icon_type=self.icon_type, size=30)
        self.icon_btn.setEnabled(False)
        layout.addWidget(self.icon_btn)
        self.lbl = QLabel(label)
        self.lbl.setObjectName("navLabel")
        self.lbl.setFont(QFont("", 11))
        self.lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.lbl)
        self.chev = QLabel("›")
        self.chev.setFixedWidth(12)
        self.chev.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.chev)
        self.setCursor(Qt.PointingHandCursor)
        self.installEventFilter(self)

    def set_icon_color(self, color):
        self.icon_btn.set_icon_color(color)
        if isinstance(color, QColor):
            c = color
        else:
            c = QColor(color)
        self.lbl.setStyleSheet(f"color: {c.name()};")

    def set_hover_style(self, style_str: str):
        self._hover_style = style_str

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.selected:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            rect = self.rect()
            width = 12
            path = QPainterPath()
            path.moveTo(0, 0)
            h = rect.height()
            cp1 = QPoint(width, int(h * 0.25))
            cp2 = QPoint(0, int(h * 0.5))
            path.quadTo(cp1, cp2)
            cp3 = QPoint(width, int(h * 0.75))
            cp4 = QPoint(0, int(h))
            path.quadTo(cp3, cp4)
            color = self.palette().highlight().color()
            color.setAlpha(200)
            p.fillPath(path, color)
            p.end()

    def mouseReleaseEvent(self, event):
        w = self
        while w and not isinstance(w, NavSection) and not isinstance(w, InterfaceWindow):
            w = w.parent()
        if isinstance(w, NavSection):
            w._on_shortcut_clicked(self)
        elif isinstance(w, InterfaceWindow):
            w._on_shortcut_trigger(self)
        super().mouseReleaseEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.setStyleSheet(self._hover_style)
        elif event.type() == QEvent.Leave:
            self.setStyleSheet("")
        return super().eventFilter(obj, event)


# ---------------- NavSection ----------------
class NavSection(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.items = []
        self.collapsed = False
        main_v = QVBoxLayout()
        main_v.setContentsMargins(4, 4, 4, 4)
        main_v.setSpacing(4)
        self.setLayout(main_v)
        hdr = QWidget()
        hdr_l = QHBoxLayout()
        hdr_l.setContentsMargins(6, 4, 6, 4)
        hdr.setLayout(hdr_l)
        self.toggle_btn = QPushButton("▾")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle)
        hdr_l.addWidget(self.toggle_btn)
        lbl = QLabel(title)
        lbl.setFont(QFont("", 10, QFont.Bold))
        lbl.setObjectName("sectionLabel")
        hdr_l.addWidget(lbl)
        hdr_l.addStretch()
        main_v.addWidget(hdr)
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setContentsMargins(2, 2, 2, 2)
        self.container_layout.setSpacing(2)
        self.container.setLayout(self.container_layout)
        main_v.addWidget(self.container)

    def add_shortcut(self, key: str, label: str, icon_type="folder"):
        item = ShortcutItem(key, label, icon_type, parent=self.container)
        self.container_layout.addWidget(item)
        self.items.append(item)
        return item

    def _toggle(self):
        self.collapsed = not self.collapsed
        self.container.setVisible(not self.collapsed)
        self.toggle_btn.setText("▸" if self.collapsed else "▾")

    def _deselect_all(self):
        for it in self.items:
            it.selected = False
            it.update()

    def _on_shortcut_clicked(self, item: ShortcutItem):
        root = self
        while root and not isinstance(root, InterfaceWindow):
            root = root.parent()
        if isinstance(root, InterfaceWindow):
            root.handle_nav_activation(item.key, item.label)
        self._deselect_all()
        item.selected = True
        item.update()


# ---------------- InterfaceWindow ----------------
class InterfaceWindow(QMainWindow):
    def __init__(self, dados_usuario, parent=None):
        super().__init__(parent)
        self.dados_usuario = dados_usuario
        nome = self.dados_usuario.get("nome", "Usuário")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.tema_atual = "dark"
        self.cor_fundo = None
        self.cor_destaque = None
        self.imagem_fundo = None
        self._tmp_image_path = None
        self.imagem_opacity = 0.8
        self._drag_pos = None
        self._is_dragging = False
        # atualizar PAGE_MAP no arquivo se necessário
        self.page_modules_map: Dict[str, str] = dict(PAGE_MAP)
        self.neko = None
        self.setWindowTitle("DevHive")
        self.showMaximized()
        self.init_ui()
        if hasattr(self, "combo_tema"):
            self.combo_tema.setCurrentText(self.tema_atual.capitalize())
        self.aplicar_tema_padrao()
        QTimer.singleShot(120, self._try_init_neko)

    # ================= UI =================
    def init_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root_v = QVBoxLayout()
        root_v.setContentsMargins(8, 8, 8, 8)
        central.setLayout(root_v)
        self.header = QFrame()
        self.header.setObjectName("header")
        header_h = QHBoxLayout()
        header_h.setContentsMargins(6, 6, 6, 6)
        header_h.setSpacing(8)
        self.header.setLayout(header_h)
        self.btn_toggle_nav = QPushButton("≡")
        self.btn_toggle_nav.setFixedSize(36, 28)
        self.btn_toggle_nav.clicked.connect(self.toggle_navbar)
        header_h.addWidget(self.btn_toggle_nav)
        self.titulo = QLabel("DevHive")
        self.titulo.setObjectName("titulo")
        self.titulo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.titulo.setAlignment(Qt.AlignCenter)
        self.titulo.setFont(QFont("", 16, QFont.Bold))
        header_h.addWidget(self.titulo, 1)
        self.btn_min = QPushButton("—"); self.btn_min.setFixedSize(34, 24); self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max = QPushButton("▢"); self.btn_max.setFixedSize(30, 30); self.btn_max.clicked.connect(self._toggle_max_restore)
        self.btn_close = QPushButton("✕"); self.btn_close.setFixedSize(34, 24); self.btn_close.clicked.connect(self.close)
        self.btn_min.setObjectName("winMin"); self.btn_max.setObjectName("winMax"); self.btn_close.setObjectName("winClose")
        header_h.addWidget(self.btn_min); header_h.addWidget(self.btn_max); header_h.addWidget(self.btn_close)
        root_v.addWidget(self.header)
        center = QFrame()
        center.setObjectName("centerFrame")
        center_h = QHBoxLayout()
        center_h.setContentsMargins(0, 0, 0, 0)
        center.setLayout(center_h)
        self.navbar = QFrame()
        self.navbar.setObjectName("navbar")
        self.navbar.setFixedWidth(300)
        nav_v = QVBoxLayout()
        nav_v.setContentsMargins(8, 8, 8, 8)
        nav_v.setSpacing(10)
        self.navbar.setLayout(nav_v)
        self.lbl_profile = QLabel("Profile (foto aqui)")
        self.lbl_profile.setFont(QFont("", 12))
        nav_v.addWidget(self.lbl_profile)
        icons_frame = QFrame()
        icons_layout = QVBoxLayout()
        icons_layout.setContentsMargins(0, 0, 0, 0)
        icons_layout.setSpacing(4)
        icons_frame.setLayout(icons_layout)
        row_icons = QHBoxLayout()
        row_icons.setSpacing(16)
        self.icon_palette = VectorIconButton("brush", size=34)
        self.icon_palette.clicked.connect(self._open_personalizacao)
        self.icon_gear = VectorIconButton("gear", size=34)
        self.icon_gear.clicked.connect(self._abrir_configuracoes)
        row_icons.addWidget(self.icon_palette, alignment=Qt.AlignCenter)
        row_icons.addWidget(self.icon_gear, alignment=Qt.AlignCenter)
        icons_layout.addLayout(row_icons)
        row_labels = QHBoxLayout()
        row_labels.setSpacing(16)
        lbl_palette = QLabel("Personalização"); lbl_palette.setAlignment(Qt.AlignCenter)
        lbl_gear = QLabel("Configurações"); lbl_gear.setAlignment(Qt.AlignCenter)
        row_labels.addWidget(lbl_palette); row_labels.addWidget(lbl_gear)
        icons_layout.addLayout(row_labels)
        nav_v.addWidget(icons_frame)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("navContent")
        self.scroll.setWidget(self.scroll_content)
        self.nav_layout = QVBoxLayout()
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(6)
        self.scroll_content.setLayout(self.nav_layout)
        nav_v.addWidget(self.scroll, 1)
        sections = [
            ("Seção mestre", [("chat", "Chat IA", "chat"), ("dashboard", "Painel (Dashboard)", "dashboard")]),
            ("Fluxos", [("kanbans", "Painéis Kanban", "kanban")]),
            ("Agentes", [("agents_monitor", "Monitoramento de Agentes", "monitor")])
        ]
        self._nav_sections = []
        for sec_title, items in sections:
            sec = NavSection(sec_title, parent=self.scroll_content)
            for key, label, icon in items:
                sec.add_shortcut(key, label, icon)
            self.nav_layout.addWidget(sec)
            self._nav_sections.append(sec)
        self.nav_layout.addStretch()
        center_h.addWidget(self.navbar)
        self.main = QFrame()
        self.main.setObjectName("main")
        main_v = QVBoxLayout()
        main_v.setContentsMargins(12, 12, 12, 12)
        self.main.setLayout(main_v)
        self.main_header = QLabel("Nome do atalho atual")
        self.main_header.setObjectName("mainHeader")
        self.main_header.setFont(QFont("", 14, QFont.Bold))
        main_v.addWidget(self.main_header)
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_container.setLayout(self.content_layout)
        self.placeholder_label = QLabel("Área principal — módulos irão aqui.")
        self.placeholder_label.setWordWrap(True)
        self.placeholder_label.setFont(QFont("", 12))
        self.content_layout.addWidget(self.placeholder_label)
        main_v.addWidget(self.content_container)
        main_v.addStretch()
        center_h.addWidget(self.main, 1)
        self.criar_painel_customizacao()
        center_h.addWidget(self.painel)
        root_v.addWidget(center, 1)
        if self._nav_sections:
            first = self._nav_sections[0]
            if first.items:
                first.items[0].selected = True
                first.items[0].update()
                self.handle_nav_activation(first.items[0].key, first.items[0].label)

    def criar_painel_customizacao(self):
        self.painel = QFrame()
        self.painel.setObjectName("painel_customizacao")
        self.painel.setFixedWidth(420)
        self.painel.hide()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.painel.setLayout(layout)
        phdr = QWidget()
        phdr_l = QHBoxLayout()
        phdr_l.setContentsMargins(0, 0, 0, 0)
        phdr.setLayout(phdr_l)
        phdr_lbl = QLabel("Personalização")
        phdr_lbl.setFont(QFont("", 12, QFont.Bold))
        phdr_l.addWidget(phdr_lbl)
        phdr_l.addStretch()
        self.btn_close_panel = QToolButton()
        self.btn_close_panel.setText("✕")
        self.btn_close_panel.setCursor(Qt.PointingHandCursor)
        self.btn_close_panel.setFixedSize(22, 22)
        self.btn_close_panel.clicked.connect(lambda: self.painel.setVisible(False))
        phdr_l.addWidget(self.btn_close_panel)
        layout.addWidget(phdr)
        layout.addWidget(QLabel("Modo:"))
        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["Dark", "Light"])
        self.combo_tema.currentTextChanged.connect(self.trocar_tema)
        layout.addWidget(self.combo_tema)
        layout.addWidget(QLabel("Aplicar em:"))
        self.combo_escopo = QComboBox()
        self.combo_escopo.addItems(["Global", "Navbar", "Header", "Main"])
        layout.addWidget(self.combo_escopo)
        btn_cor_fundo = QPushButton("Escolher cor de fundo")
        btn_cor_fundo.clicked.connect(self.escolher_cor_fundo)
        layout.addWidget(btn_cor_fundo)
        btn_cor_destaque = QPushButton("Escolher cor destaque")
        btn_cor_destaque.clicked.connect(self.escolher_cor_destaque)
        layout.addWidget(btn_cor_destaque)
        btn_imagem = QPushButton("Selecionar imagem de fundo")
        btn_imagem.clicked.connect(self.escolher_imagem)
        layout.addWidget(btn_imagem)
        layout.addWidget(QLabel("Transparência da imagem (%)"))
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(int(self.imagem_opacity * 100))
        self.slider_opacity.valueChanged.connect(self.on_opacity_changed)
        layout.addWidget(self.slider_opacity)
        layout.addStretch()

    def handle_nav_activation(self, key: str, label: str):
        self.main_header.setText(label)
        try:
            self.load_shortcut_module(key)
        except Exception:
            traceback.print_exc()
            self.clear_content_container()
            lbl = QLabel(f"Atalho selecionado: {label} (key={key})")
            lbl.setWordWrap(True)
            lbl.setFont(QFont("", 12))
            self.content_layout.addWidget(lbl)
        for sec in self._nav_sections:
            for it in sec.items:
                if it.key == key:
                    sec._deselect_all()
                    it.selected = True
                    it.update()
                    if sec.collapsed:
                        sec._toggle()
                else:
                    it.selected = False
                    it.update()

    def _open_personalizacao(self):
        self.painel.setVisible(True)

    def _abrir_configuracoes(self):
        QMessageBox.information(self, "Configurações", "Aba de configurações (a implementar).")

    def toggle_navbar(self):
        self.navbar.setVisible(not self.navbar.isVisible())

    def trocar_tema(self, texto):
        self.tema_atual = texto.lower()
        self.aplicar_estilo()

    def escolher_cor_fundo(self):
        cor = QColorDialog.getColor()
        if cor.isValid():
            self.cor_fundo = cor.name()
            self.aplicar_estilo()

    def escolher_cor_destaque(self):
        cor = QColorDialog.getColor()
        if cor.isValid():
            self.cor_destaque = cor.name()
            self.aplicar_estilo()

    def escolher_imagem(self):
        try:
            arq, _ = QFileDialog.getOpenFileName(self, "Selecionar imagem", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
            if arq:
                self.imagem_fundo = arq
                self._update_temporary_image_with_opacity()
                self.aplicar_estilo()
        except Exception:
            traceback.print_exc()
            QMessageBox.warning(self, "Erro", "Não foi possível carregar a imagem.")

    def on_opacity_changed(self, val):
        self.imagem_opacity = max(0.0, min(1.0, val / 100.0))
        if self.imagem_fundo:
            try:
                self._update_temporary_image_with_opacity()
                self.aplicar_estilo()
            except Exception:
                traceback.print_exc()

    def _update_temporary_image_with_opacity(self):
        if not self.imagem_fundo or not os.path.exists(self.imagem_fundo):
            return
        original = QPixmap(self.imagem_fundo)
        if original.isNull():
            raise ValueError("Formato de imagem inválido.")
        w, h = original.width(), original.height()
        composed = QPixmap(w, h)
        composed.fill(Qt.transparent)
        p = QPainter(composed)
        p.setOpacity(self.imagem_opacity)
        p.drawPixmap(0, 0, original)
        p.end()
        if self._tmp_image_path and os.path.exists(self._tmp_image_path):
            try:
                os.remove(self._tmp_image_path)
            except Exception:
                pass
        fd, tmp = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        saved = composed.save(tmp, "PNG")
        if not saved:
            raise IOError("Falha ao salvar imagem temporária.")
        self._tmp_image_path = tmp

    def clear_content_container(self):
        for i in reversed(range(self.content_layout.count())):
            w = self.content_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

    def load_shortcut_module(self, key: str):
        """
        Carrega dinamicamente módulos de página.
        Estratégia:
         - tenta mapping explícito em self.page_modules_map
         - tenta caminhos em interface.janelas.*, interface.*, pages.*
         - aceita classes MainWidget, MainPage, padrões como Painel<...>, <Key>Widget, Window
         - como fallback usa a primeira classe do módulo que seja subclass de QWidget
        """
        self.clear_content_container()
        module_candidates = []
        mapped = self.page_modules_map.get(key)
        if mapped:
            module_candidates.append(mapped)
        # convensões possíveis dentro de interface/ e interface/janelas/
        module_candidates.extend([
            f"interface.{key}",
            f"interface.{key}_ui",
            f"interface.painel_{key}",
            f"interface.{key.replace('-', '_')}",
            # novos candidatos para a pasta janelas (nova organização)
            f"interface.janelas.{key}",
            f"interface.janelas.painel_{key}",
            f"interface.janelas.{key.replace('-', '_')}",
        ])

        loaded = False
        last_exc = None
        for module_name in module_candidates:
            try:
                mod = importlib.import_module(module_name)
                cls = None
                # 1) nomes explícitos preferenciais
                if hasattr(mod, "MainWidget"):
                    cls = getattr(mod, "MainWidget")
                elif hasattr(mod, "MainPage"):
                    cls = getattr(mod, "MainPage")
                else:
                    # 2) tentar convenções a partir da key (CamelCase)
                    base = ''.join(part.capitalize() for part in key.replace('-', '_').split('_') if part)
                    candidates = [base, "Painel" + base, base + "Widget", base + "Window", base + "Page"]
                    for cname in candidates:
                        if hasattr(mod, cname):
                            obj = getattr(mod, cname)
                            if inspect.isclass(obj):
                                cls = obj
                                break
                # 3) fallback: primeira classe do módulo que herde QWidget (definida no próprio módulo)
                if cls is None:
                    for name, obj in inspect.getmembers(mod, inspect.isclass):
                        # garantir que seja definida no módulo (evitar classes importadas)
                        if obj.__module__ != mod.__name__:
                            continue
                        try:
                            if issubclass(obj, QWidget):
                                cls = obj
                                break
                        except Exception:
                            continue
                if cls:
                    # tenta instanciar (aceita dados_usuario quando possível)
                    try:
                        page_widget = cls(self.dados_usuario)
                    except TypeError:
                        try:
                            page_widget = cls()
                        except Exception as e:
                            raise
                    self.content_layout.addWidget(page_widget)
                    loaded = True
                    break
            except ModuleNotFoundError:
                continue
            except Exception as e:
                last_exc = e
                traceback.print_exc()
                continue
        if not loaded:
            if last_exc:
                lbl = QLabel(f"Erro ao carregar módulo para '{key}': {last_exc}")
            else:
                lbl = QLabel(f"Atalho selecionado: {key} — módulo de página não encontrado.")
            lbl.setWordWrap(True)
            lbl.setFont(QFont("", 12))
            self.content_layout.addWidget(lbl)

    def aplicar_tema_padrao(self):
        self.aplicar_estilo()

    def aplicar_estilo(self):
        try:
            if self.tema_atual == "dark":
                default_bg = "#000000"
                default_fg = "#FFFFFF"
                default_main_bg = "#0b0b0b"
                default_accent = default_fg
                header_bg = "#050505"
                nav_bg = "#050505"
            else:
                default_bg = "#FFFFFF"
                default_fg = "#000000"
                default_main_bg = "#f5f5f5"
                default_accent = default_fg
                header_bg = "#f0f0f0"
                nav_bg = "#f0f0f0"
            escopo = self.combo_escopo.currentText() if hasattr(self, "combo_escopo") else "Global"
            bg = self.cor_fundo or default_bg
            fg = default_fg
            main_bg = default_main_bg
            nav_background = nav_bg
            header_background = header_bg
            accent = self.cor_destaque or default_accent
            if self.cor_fundo:
                if escopo == "Global":
                    bg = self.cor_fundo
                    main_bg = self.cor_fundo
                    nav_background = self.cor_fundo
                    header_background = self.cor_fundo
                elif escopo == "Navbar":
                    nav_background = self.cor_fundo
                elif escopo == "Header":
                    header_background = self.cor_fundo
                elif escopo == "Main":
                    main_bg = self.cor_fundo
            def qcol(c):
                return QColor(c) if not isinstance(c, QColor) else c
            def rgba_str(qc: QColor, alpha_float: float):
                r, g, b = qc.red(), qc.green(), qc.blue()
                return f"rgba({r},{g},{b},{alpha_float})"
            bg_qc = qcol(bg)
            fg_qc = qcol(fg)
            main_bg_qc = qcol(main_bg)
            nav_bg_qc = qcol(nav_background)
            header_bg_qc = qcol(header_background)
            accent_qc = qcol(accent)
            dir_here = os.path.dirname(os.path.abspath(__file__))
            tema_path = os.path.join(dir_here, "style", "tema.css")
            final_qss = ""
            if os.path.exists(tema_path):
                with open(tema_path, "r", encoding="utf-8") as f:
                    css_template = f.read()
                css = css_template.replace("__BG__", bg) \
                                  .replace("__FG__", fg) \
                                  .replace("__MAIN_BG__", main_bg) \
                                  .replace("__MAIN_FG__", fg) \
                                  .replace("__ACCENT__", accent) \
                                  .replace("__HEADER_BG__", header_background) \
                                  .replace("__NAV_BG__", nav_background)
                final_qss = css
            else:
                border_alpha = 0.12
                hover_alpha = 0.045 if self.tema_atual == "dark" else 0.06
                final_qss = f"""
                QWidget#centralWidget {{ background-color: {bg}; color: {fg}; font-size: 13px; }}
                QWidget#main {{ background-color: {main_bg}; color: {fg}; }}
                QWidget#header {{ background-color: {header_background}; color: {fg}; }}
                QWidget#navbar {{ background-color: {nav_background}; color: {fg}; }}
                QWidget#navContent {{ background-color: {nav_background}; color: {fg}; }}
                QLabel#titulo {{ font-weight: 700; color: {fg}; font-size: 18px; }}
                QLabel#mainHeader {{ font-weight: 600; color: {fg}; font-size: 16px; }}
                QLabel#navLabel {{ color: {fg}; font-size: 13px; }}
                QLabel#sectionLabel {{ color: {fg}; font-size: 13px; }}
                QFrame#painel_customizacao {{ background-color: {main_bg}; color: {fg}; }}
                QScrollArea {{ background-color: {nav_background}; }}
                QFrame#navbar {{ border-right: 1px solid {rgba_str(accent_qc, border_alpha)}; }}
                QPushButton {{ border: 1px solid {rgba_str(accent_qc, border_alpha)}; border-radius: 6px; padding: 6px; color: {accent_qc.name()}; background: transparent; font-size:13px }}
                QPushButton:hover {{ background-color: {rgba_str(fg_qc, hover_alpha)}; }}
                QPushButton#winMin {{ color: {fg}; border: 1px solid {rgba_str(fg_qc, 0.12)}; background: {rgba_str(fg_qc, 0.02)}; }}
                QPushButton#winMax {{ color: {fg}; border: 1px solid {rgba_str(fg_qc, 0.06)}; background: {rgba_str(fg_qc, 0.01)}; }}
                QPushButton#winClose {{ color: {fg}; border: 1px solid rgba(255,0,0,0.25); background: rgba(255,0,0,0.06); }}
                """
            caminho = None
            if self._tmp_image_path and os.path.exists(self._tmp_image_path):
                caminho = self._tmp_image_path
            elif self.imagem_fundo and os.path.exists(self.imagem_fundo):
                caminho = self.imagem_fundo
            if caminho:
                url = QUrl.fromLocalFile(os.path.abspath(caminho)).toString()
                if escopo == "Global":
                    final_qss += f"""
                    QWidget#centralWidget {{
                        background-image: url("{url}");
                        background-repeat: no-repeat;
                        background-position: center;
                        background-size: cover;
                    }}
                    """
                elif escopo == "Navbar":
                    final_qss += f"""
                    QWidget#navbar {{
                        background-image: url("{url}");
                        background-repeat: no-repeat;
                        background-position: center;
                        background-size: cover;
                    }}
                    """
                elif escopo == "Header":
                    final_qss += f"""
                    QWidget#header {{
                        background-image: url("{url}");
                        background-repeat: no-repeat;
                        background-position: center;
                        background-size: cover;
                    }}
                    """
                elif escopo == "Main":
                    final_qss += f"""
                    QWidget#main {{
                        background-image: url("{url}");
                        background-repeat: no-repeat;
                        background-position: center;
                        background-size: cover;
                    }}
                    """
            self.setStyleSheet(final_qss)
            self._apply_graphics_glow(accent_qc, fg_qc)
            icon_bg_alpha = 0.06
            icon_bg_qc = QColor(fg_qc)
            icon_bg_qc.setAlphaF(icon_bg_alpha)
            self.icon_palette.set_bg_color(icon_bg_qc)
            self.icon_gear.set_bg_color(icon_bg_qc)
            try:
                self.icon_palette.set_icon_color(accent_qc)
                self.icon_gear.set_icon_color(accent_qc)
            except Exception:
                pass
            if self.tema_atual == "dark":
                hover_bg = rgba_str(fg_qc, 0.02)
            else:
                hover_bg = rgba_str(QColor(0, 0, 0), 0.04)
            for sec in self._nav_sections:
                for it in sec.items:
                    try:
                        it.icon_btn.set_icon_color(accent_qc)
                    except Exception:
                        pass
                    if it.selected:
                        it.lbl.setStyleSheet(f"color: {accent_qc.name()};")
                        it.icon_btn.set_bg_color(QColor(accent_qc.red(), accent_qc.green(), accent_qc.blue(), 28))
                    else:
                        it.lbl.setStyleSheet(f"color: {fg_qc.name()};")
                        default_icon_bg = QColor(fg_qc.red(), fg_qc.green(), fg_qc.blue(), 12)
                        it.icon_btn.set_bg_color(default_icon_bg)
                    it.set_hover_style(f"background: {hover_bg};")
            if self.tema_atual == "dark":
                self.btn_min.setStyleSheet("color: white;")
                self.btn_max.setStyleSheet("color: white;")
                self.btn_close.setStyleSheet("color: white;")
            else:
                self.btn_min.setStyleSheet("")
                self.btn_max.setStyleSheet("")
                self.btn_close.setStyleSheet("")
            try:
                app = QApplication.instance()
                if app:
                    pal = app.palette()
                    pal.setColor(QPalette.Window, bg_qc)
                    pal.setColor(QPalette.WindowText, fg_qc)
                    pal.setColor(QPalette.Base, main_bg_qc)
                    pal.setColor(QPalette.Text, fg_qc)
                    pal.setColor(QPalette.Button, main_bg_qc)
                    pal.setColor(QPalette.ButtonText, fg_qc)
                    pal.setColor(QPalette.Highlight, accent_qc)
                    if self.tema_atual == "dark":
                        pal.setColor(QPalette.HighlightedText, QColor("#000000"))
                    else:
                        pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
                    app.setPalette(pal)
            except Exception:
                traceback.print_exc()
        except Exception:
            traceback.print_exc()
            QMessageBox.warning(self, "Erro ao aplicar estilo",
                                "Ocorreu um erro ao aplicar o tema (veja console).")

    def _apply_graphics_glow(self, accent: Optional[QColor], fg: Optional[QColor]):
        try:
            try:
                glow_color = QColor(accent) if accent is not None else QColor("#FFFFFF")
            except Exception:
                glow_color = QColor("#FFFFFF")

            def make_effect(radius=18, blur=18, alpha=200):
                c = QColor(glow_color)
                c.setAlpha(alpha)
                eff = QGraphicsDropShadowEffect()
                eff.setBlurRadius(blur)
                eff.setColor(c)
                eff.setOffset(0, 0)
                return eff

            if hasattr(self, "titulo") and self.titulo:
                self.titulo.setGraphicsEffect(make_effect(radius=18, blur=20, alpha=200))

            if hasattr(self, "main_header") and self.main_header:
                self.main_header.setGraphicsEffect(make_effect(radius=14, blur=16, alpha=160))

            for w in (self.btn_min, self.btn_max, self.btn_close, self.btn_toggle_nav):
                if hasattr(self, w.objectName()) or w:
                    try:
                        w.setGraphicsEffect(make_effect(radius=8, blur=10, alpha=140))
                    except Exception:
                        pass

            for icon_btn in (self.icon_palette, self.icon_gear):
                if icon_btn:
                    try:
                        icon_btn.setGraphicsEffect(make_effect(radius=12, blur=14, alpha=180))
                    except Exception:
                        pass

        except Exception:
            traceback.print_exc()

    def _toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.globalPos()
            local_pos = self.mapFromGlobal(pos)
            if 0 <= local_pos.y() <= self.header.height():
                self._is_dragging = True
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_is_dragging", False) and event.buttons() & Qt.LeftButton:
            if self._drag_pos:
                self.move(event.globalPos() - self._drag_pos)
                event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            QTimer.singleShot(0, self._handle_window_state_change)
        super().changeEvent(event)

    def _handle_window_state_change(self):
        if self.windowState() & Qt.WindowMinimized:
            return
        if self.isMaximized():
            return
        try:
            self.resize(900, 900)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            if self._tmp_image_path and os.path.exists(self._tmp_image_path):
                os.remove(self._tmp_image_path)
        except Exception:
            pass
        super().closeEvent(event)

    def _try_init_neko(self):
        try:
            mod = importlib.import_module("interface.objeto.widgets_neko")
            if not hasattr(mod, "NekoOrb"):
                return
            NekoOrb = getattr(mod, "NekoOrb")
            parent_candidate = None
            try:
                parent_candidate = self.centralWidget()
            except Exception:
                parent_candidate = None
            instance = None
            try:
                if parent_candidate is not None:
                    instance = NekoOrb(parent=parent_candidate)
                else:
                    instance = NekoOrb(parent=self)
            except TypeError:
                try:
                    instance = NekoOrb(parent=self)
                except Exception:
                    try:
                        instance = NekoOrb()
                    except Exception as e:
                        raise e
            self.neko = instance
            try:
                if self.neko.parent() is None:
                    if parent_candidate is not None:
                        self.neko.setParent(parent_candidate)
                    else:
                        self.neko.setParent(self)
            except Exception:
                pass
            try:
                if self.neko.parent() is not None:
                    self.neko.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
                else:
                    self.neko.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                self.neko.setAttribute(Qt.WA_TranslucentBackground, True)
            except Exception:
                pass
            try:
                w = max(80, self.neko.width() or 120)
                h = max(80, self.neko.height() or 120)
                if w == 0 or h == 0:
                    sh = self.neko.sizeHint()
                    w = sh.width() or 120
                    h = sh.height() or 120
                self.neko.setFixedSize(w, h)
            except Exception:
                pass
            try:
                self.neko.show()
                self.neko.raise_()
            except Exception:
                pass
            QTimer.singleShot(80, self._position_neko_bottom_right)
        except ModuleNotFoundError:
            # tentar nome alternativo (widgets_neko em interface)
            try:
                mod = importlib.import_module("interface.objeto.widgets_neko")
                if hasattr(mod, "NekoOrb"):
                    NekoOrb = getattr(mod, "NekoOrb")
                    self.neko = NekoOrb(parent=self.centralWidget() if hasattr(self, "centralWidget") else self)
                    self.neko.show()
                    QTimer.singleShot(80, self._position_neko_bottom_right)
            except Exception:
                return
        except Exception as e:
            traceback.print_exc()
            print("Erro ao inicializar NekoOrb:", e)
            return

    def _position_neko_bottom_right(self):
        try:
            if not self.neko:
                return
            margin_x = 20
            margin_y = 40
            central = self.centralWidget() if hasattr(self, "centralWidget") else None
            if central is not None and self.neko.parent() is not None and (self.neko.parent() is central or self.neko.parent() is self):
                try:
                    if self.neko.parent() is central:
                        px = max(0, central.width() - self.neko.width() - margin_x)
                        py = max(0, central.height() - self.neko.height() - margin_y)
                        self.neko.move(px, py)
                        return
                    elif self.neko.parent() is self:
                        central_tl_global = central.mapToGlobal(central.rect().topLeft())
                        nx_global = central_tl_global.x() + central.width() - self.neko.width() - margin_x
                        ny_global = central_tl_global.y() + central.height() - self.neko.height() - margin_y
                        local_pos = self.mapFromGlobal(QPoint(nx_global, ny_global))
                        self.neko.move(local_pos)
                        return
                except Exception:
                    pass
            try:
                win_rect = self.geometry()
                nx = max(0, win_rect.width() - self.neko.width() - margin_x)
                ny = max(0, win_rect.height() - self.neko.height() - margin_y)
                try:
                    self.neko.move(nx, ny)
                except Exception:
                    global_x = self.mapToGlobal(QPoint(0, 0)).x() + nx
                    global_y = self.mapToGlobal(QPoint(0, 0)).y() + ny
                    self.neko.move(self.mapFromGlobal(QPoint(global_x, global_y)))
            except Exception:
                traceback.print_exc()
            try:
                self.neko.show()
                self.neko.raise_()
            except Exception:
                pass
        except Exception:
            traceback.print_exc()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    dados_teste = {"nome": "Teste"}
    w = InterfaceWindow(dados_teste)
    w.show()
    sys.exit(app.exec_())
