from PyQt5.QtCore import QEvent, QPoint, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from interface.window.constants import ICON_KEY_TO_TYPE


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
                p.drawEllipse(QRectF(-r / 2.0, -r / 2.0, r, r))
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
        while w:
            if isinstance(w, NavSection):
                w._on_shortcut_clicked(self)
                break
            if hasattr(w, "handle_nav_activation"):
                w.handle_nav_activation(self.key, self.label)
                break
            w = w.parent()
        super().mouseReleaseEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.setStyleSheet(self._hover_style)
        elif event.type() == QEvent.Leave:
            self.setStyleSheet("")
        return super().eventFilter(obj, event)


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
        while root and not hasattr(root, "handle_nav_activation"):
            root = root.parent()
        if root and hasattr(root, "handle_nav_activation"):
            root.handle_nav_activation(item.key, item.label)
        self._deselect_all()
        item.selected = True
        item.update()
