import os
import traceback
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QPainterPath, QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout


class ProfileMixin:
    def _create_profile_widget(self) -> QWidget:
        w = QFrame()
        w.setObjectName("profileFrame")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        compact = QWidget()
        compact_layout = QVBoxLayout(compact)
        compact_layout.setContentsMargins(0, 0, 0, 0)
        compact_layout.setSpacing(6)
        compact_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self._avatar_size = 96
        self._profile_avatar = QLabel()
        self._profile_avatar.setFixedSize(self._avatar_size, self._avatar_size)
        self._profile_avatar.setAlignment(Qt.AlignCenter)

        self._lbl_name = QLabel()
        self._lbl_name.setFont(QFont("", 12, QFont.Bold))
        self._lbl_name.setAlignment(Qt.AlignCenter)

        self._lbl_cargo = QLabel()
        self._lbl_cargo.setFont(QFont("", 10))
        self._lbl_cargo.setAlignment(Qt.AlignCenter)

        self._btn_toggle_profile = QPushButton("Ver perfil")
        self._btn_toggle_profile.setCursor(Qt.PointingHandCursor)
        self._btn_toggle_profile.setFixedHeight(28)
        self._btn_toggle_profile.clicked.connect(self._toggle_profile_view)

        compact_layout.addWidget(self._profile_avatar, alignment=Qt.AlignHCenter)
        compact_layout.addWidget(self._lbl_name)
        compact_layout.addWidget(self._lbl_cargo)
        compact_layout.addWidget(self._btn_toggle_profile, alignment=Qt.AlignHCenter)

        self._compact_profile_container = compact
        layout.addWidget(compact)
        return w

    def _refresh_profile_widget(self):
        d = self.dados_usuario or {}
        nome = d.get("nome") or d.get("nome_exibicao") or d.get("display_name") or "Usuário"
        email = d.get("email") or d.get("mail") or ""
        papel = d.get("papel") or d.get("role") or ""
        cargo = d.get("cargo") or d.get("position") or ""
        foto = d.get("foto") or d.get("avatar") or ""

        self._lbl_name.setText(str(nome))
        self._lbl_cargo.setText(str(cargo) if cargo else "")

        pix = self._avatar_pixmap_circular(foto, nome, size=self._avatar_size)
        if pix:
            self._profile_avatar.setPixmap(pix)
        else:
            self._profile_avatar.clear()

        if self._profile_card:
            try:
                lbls = getattr(self._profile_card, "_field_labels", {})
                if "nome" in lbls:
                    lbls["nome"].setText(str(nome))
                if "email" in lbls:
                    lbls["email"].setText(str(email))
                if "papel" in lbls:
                    lbls["papel"].setText(str(papel))
                if "cargo" in lbls:
                    lbls["cargo"].setText(str(cargo))
                if "mini_avatar" in lbls:
                    mini = self._avatar_pixmap_circular(foto, nome, size=48)
                    if mini:
                        lbls["mini_avatar"].setPixmap(mini)
                    else:
                        lbls["mini_avatar"].clear()
            except Exception:
                traceback.print_exc()

    def _avatar_pixmap_circular(self, foto_path: Optional[str], nome: str, size: int = 96) -> Optional[QPixmap]:
        try:
            if foto_path and isinstance(foto_path, str) and os.path.exists(foto_path):
                orig = QPixmap(foto_path)
                if not orig.isNull():
                    scaled = orig.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    out = QPixmap(size, size)
                    out.fill(Qt.transparent)
                    p = QPainter(out)
                    p.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    path.addEllipse(0, 0, size, size)
                    p.setClipPath(path)
                    sw, sh = scaled.width(), scaled.height()
                    sx, sy = max(0, (sw - size) // 2), max(0, (sh - size) // 2)
                    p.drawPixmap(0, 0, scaled.copy(sx, sy, size, size))
                    p.end()
                    return out
        except Exception:
            pass

        initials = "U"
        try:
            parts = [p for p in nome.strip().split() if p]
            if len(parts) == 1:
                initials = parts[0][0].upper()
            elif len(parts) >= 2:
                initials = (parts[0][0] + parts[-1][0]).upper()
        except Exception:
            initials = "U"

        color = self._color_from_string(nome)
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, size, size)
        f = QFont()
        f.setBold(True)
        f.setPointSize(int(size * 0.36))
        p.setFont(f)
        p.setPen(QColor(255, 255, 255))
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(initials)
        th = fm.height()
        p.drawText((size - tw) // 2, (size + th // 2) // 2, initials)
        p.end()
        return pix

    def _color_from_string(self, s: str) -> str:
        if not s:
            return "#555555"
        h = 0
        for ch in s:
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        r = int(((h >> 16) & 0xFF) * 0.7)
        g = int(((h >> 8) & 0xFF) * 0.7)
        b = int((h & 0xFF) * 0.7)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _insert_if_missing(self, layout: QVBoxLayout, widget: QWidget, pos: int = 0):
        for i in range(layout.count()):
            if layout.itemAt(i).widget() is widget:
                return
        layout.insertWidget(pos, widget)

    def _show_expanded_profile(self):
        try:
            frame = self.profile_widget
            if not frame:
                return
            layout = frame.layout()
            if not layout:
                return

            if not self._profile_card:
                self._profile_card = self.view_profile_card()

            try:
                if self._compact_profile_container and self._compact_profile_container.parent() is frame:
                    self._compact_profile_container.hide()
                    try:
                        layout.removeWidget(self._compact_profile_container)
                    except Exception:
                        pass
            except Exception:
                traceback.print_exc()

            try:
                self._insert_if_missing(layout, self._profile_card, 0)
                self._profile_card.show()
                self._profile_card.raise_()
                frame.raise_()
                self.navbar.raise_()
                QTimer.singleShot(0, lambda: (frame.update(), QApplication.processEvents()))
                self._btn_toggle_profile.setText("Ocultar perfil")
            except Exception:
                traceback.print_exc()
        except Exception:
            traceback.print_exc()

    def _restore_compact_profile(self):
        try:
            frame = self.profile_widget
            if not frame:
                return
            layout = frame.layout()
            if not layout:
                return

            try:
                if self._profile_card and self._profile_card.parent() is frame:
                    self._profile_card.hide()
                    try:
                        layout.removeWidget(self._profile_card)
                    except Exception:
                        pass
                    try:
                        self._profile_card.setParent(None)
                    except Exception:
                        pass
            except Exception:
                traceback.print_exc()

            try:
                if self._compact_profile_container:
                    if self._compact_profile_container.parent() is not frame:
                        self._compact_profile_container.setParent(frame)
                    self._insert_if_missing(layout, self._compact_profile_container, 0)
                    self._compact_profile_container.show()
                    self._compact_profile_container.raise_()
                    frame.raise_()
                    self.navbar.raise_()
                    QTimer.singleShot(0, QApplication.processEvents)
                    self._btn_toggle_profile.setText("Ver perfil")
            except Exception:
                traceback.print_exc()
        except Exception:
            traceback.print_exc()

    def _toggle_profile_view(self):
        try:
            if self._profile_card and self._profile_card.isVisible():
                self._restore_compact_profile()
            else:
                self._show_expanded_profile()
        except Exception:
            traceback.print_exc()

    def view_profile_card(self) -> QFrame:
        d = self.dados_usuario or {}
        nome = d.get("nome") or d.get("nome_exibicao") or d.get("display_name") or "Usuário"
        email = d.get("email") or d.get("mail") or ""
        papel = d.get("papel") or d.get("role") or ""
        cargo = d.get("cargo") or d.get("position") or ""
        foto = d.get("foto") or d.get("avatar") or ""

        card = QFrame()
        card.setObjectName("profileCard")
        card.setFrameShape(QFrame.StyledPanel)

        v = QVBoxLayout(card)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        mini_avatar = QLabel()
        mini_avatar.setFixedSize(48, 48)
        mini_avatar.setAlignment(Qt.AlignCenter)
        mini_pix = self._avatar_pixmap_circular(foto, nome, size=48)
        if mini_pix:
            mini_avatar.setPixmap(mini_pix)
        header.addWidget(mini_avatar)

        header_txt = QVBoxLayout()
        header_txt.setSpacing(2)
        lbl_nome = QLabel(str(nome))
        lbl_nome.setObjectName("cardNome")
        lbl_nome.setFont(QFont("", 11, QFont.Bold))
        lbl_papel = QLabel(str(papel) if papel else "—")
        lbl_papel.setFont(QFont("", 9))
        header_txt.addWidget(lbl_nome)
        header_txt.addWidget(lbl_papel)

        header.addLayout(header_txt)
        header.addStretch()
        v.addLayout(header)

        def add_field(label_text: str, value_text: str):
            c = QWidget()
            cl = QVBoxLayout(c)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(2)
            lbl = QLabel(label_text)
            lbl.setProperty("fieldLabel", True)
            val = QLabel(value_text if value_text else "—")
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            cl.addWidget(lbl)
            cl.addWidget(val)
            return c, val

        row_email, val_email = add_field("Email", str(email))
        row_papel, val_papel = add_field("Papel", str(papel))
        row_cargo, val_cargo = add_field("Cargo", str(cargo))

        v.addWidget(row_email)
        v.addWidget(row_papel)
        v.addWidget(row_cargo)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Fechar")
        btn_close.setFixedHeight(26)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self._restore_compact_profile)
        btn_row.addWidget(btn_close)
        v.addLayout(btn_row)

        card._field_labels = {
            "nome": lbl_nome,
            "email": val_email,
            "papel": val_papel,
            "cargo": val_cargo,
            "mini_avatar": mini_avatar,
        }

        return card
