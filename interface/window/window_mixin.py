import importlib
import os
import traceback

from PyQt5.QtCore import QEvent, QPoint, Qt, QTimer


class WindowMixin:
    def _toggle_max_restore(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            local_pos = self.mapFromGlobal(event.globalPos())
            header = getattr(self, "header", None)
            if 0 <= local_pos.y() <= (header.height() if header else 0):
                self._is_dragging = True
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_is_dragging", False) and event.buttons() & Qt.LeftButton and getattr(self, "_drag_pos", None):
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
            if getattr(self, "_tmp_image_path", None) and os.path.exists(self._tmp_image_path):
                os.remove(self._tmp_image_path)
        except Exception:
            pass
        try:
            if getattr(self, "theme_controller", None) and hasattr(self.theme_controller, "close"):
                self.theme_controller.close()
        except Exception:
            pass
        super().closeEvent(event)

    def _try_init_neko(self):
        try:
            mod = importlib.import_module("interface.objeto.widgets_neko")
            if not hasattr(mod, "NekoOrb"):
                return
            NekoOrb = getattr(mod, "NekoOrb")
        except Exception:
            return

        parent_candidate = getattr(self, "centralWidget", lambda: None)() if hasattr(self, "centralWidget") else None
        inst = None
        for ctor_parent in (parent_candidate, self, None):
            if ctor_parent is None:
                try:
                    inst = NekoOrb()
                    break
                except Exception:
                    continue
            try:
                inst = NekoOrb(parent=ctor_parent)
                break
            except TypeError:
                try:
                    inst = NekoOrb(parent=self)
                    break
                except Exception:
                    continue
            except Exception:
                continue

        if not inst:
            return

        self.neko = inst
        try:
            if self.neko.parent() is None:
                if parent_candidate is not None:
                    self.neko.setParent(parent_candidate)
                else:
                    self.neko.setParent(self)
            self.neko.setWindowFlags(
                Qt.Widget | Qt.FramelessWindowHint
                if self.neko.parent() is not None
                else Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            )
            self.neko.setAttribute(Qt.WA_TranslucentBackground, True)
        except Exception:
            pass

        try:
            w = max(80, self.neko.width() or 120)
            h = max(80, self.neko.height() or 120)
            if w == 0 or h == 0:
                sh = self.neko.sizeHint()
                w, h = sh.width() or 120, sh.height() or 120
            self.neko.setFixedSize(w, h)
        except Exception:
            pass

        try:
            self.neko.show()
            self.neko.raise_()
        except Exception:
            pass
        QTimer.singleShot(80, self._position_neko_bottom_right)

    def _position_neko_bottom_right(self):
        try:
            if not getattr(self, "neko", None):
                return
            margin_x, margin_y = 20, 40
            central = self.centralWidget() if hasattr(self, "centralWidget") else None
            if central is not None and self.neko.parent() in (central, self):
                if self.neko.parent() is central:
                    px = max(0, central.width() - self.neko.width() - margin_x)
                    py = max(0, central.height() - self.neko.height() - margin_y)
                    self.neko.move(px, py)
                    return

                ct = central.mapToGlobal(central.rect().topLeft())
                nx = ct.x() + central.width() - self.neko.width() - margin_x
                ny = ct.y() + central.height() - self.neko.height() - margin_y
                self.neko.move(self.mapFromGlobal(QPoint(nx, ny)))
                return

            win_rect = self.geometry()
            nx = max(0, win_rect.width() - self.neko.width() - margin_x)
            ny = max(0, win_rect.height() - self.neko.height() - margin_y)
            try:
                self.neko.move(nx, ny)
            except Exception:
                gx = self.mapToGlobal(QPoint(0, 0)).x() + nx
                gy = self.mapToGlobal(QPoint(0, 0)).y() + ny
                self.neko.move(self.mapFromGlobal(QPoint(gx, gy)))
            try:
                self.neko.show()
                self.neko.raise_()
            except Exception:
                pass
        except Exception:
            traceback.print_exc()
