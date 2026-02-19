import os
import tempfile
import traceback
from typing import Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from interface.theme_engine import apply_palette, build_main_qss, build_theme_tokens


class ThemeMixin:
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
        phdr_lbl.setFont(self._font_bold(12))
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

        layout.addWidget(QLabel("Temas salvos:"))
        self.combo_temas_salvos = QComboBox()
        self.combo_temas_salvos.setToolTip("Selecione um tema salvo")
        self.combo_temas_salvos.currentIndexChanged.connect(self._on_tema_salvo_selecionado)
        layout.addWidget(self.combo_temas_salvos)

        row_btns = QHBoxLayout()
        self.btn_salvar_tema = QPushButton("Salvar tema atual")
        self.btn_salvar_tema.clicked.connect(self._on_salvar_tema)
        self.btn_def_ativo = QPushButton("Definir ativo")
        self.btn_def_ativo.clicked.connect(self._on_definir_ativo)
        row_btns.addWidget(self.btn_salvar_tema)
        row_btns.addWidget(self.btn_def_ativo)
        layout.addLayout(row_btns)

        row_btns2 = QHBoxLayout()
        self.btn_editar_tema = QPushButton("Editar nome")
        self.btn_editar_tema.clicked.connect(self._on_editar_nome_tema)
        self.btn_apagar_tema = QPushButton("Apagar tema")
        self.btn_apagar_tema.clicked.connect(self._on_apagar_tema)
        row_btns2.addWidget(self.btn_editar_tema)
        row_btns2.addWidget(self.btn_apagar_tema)
        layout.addLayout(row_btns2)

        self.btn_resetar = QPushButton("Resetar para padrão")
        self.btn_resetar.clicked.connect(self._on_resetar_para_padrao)
        layout.addWidget(self.btn_resetar)

        layout.addStretch()

        try:
            self._reload_temas_salvos()
        except Exception:
            traceback.print_exc()

    def _font_bold(self, size):
        from PyQt5.QtGui import QFont

        return QFont("", size, QFont.Bold)

    def _open_personalizacao(self):
        self.painel.setVisible(True)

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

    def _reload_temas_salvos(self):
        self.combo_temas_salvos.blockSignals(True)
        self.combo_temas_salvos.clear()
        if not self.theme_controller:
            self.combo_temas_salvos.blockSignals(False)
            return

        temas = []
        try:
            temas = self.theme_controller.list_all()
        except Exception:
            traceback.print_exc()

        self._temas_cache = temas or []
        for t in self._temas_cache:
            label = t.get("name", "—")
            if t.get("is_active"):
                label += "  (ativo)"
            self.combo_temas_salvos.addItem(label, userData=t.get("id"))
        self.combo_temas_salvos.blockSignals(False)

    def _get_selected_tema_id(self) -> Optional[int]:
        idx = self.combo_temas_salvos.currentIndex()
        if idx < 0:
            return None
        return self.combo_temas_salvos.itemData(idx)

    def _on_salvar_tema(self):
        name, ok = QInputDialog.getText(self, "Salvar tema", "Nome do tema:")
        if not ok or not name.strip():
            return

        scope = self.combo_escopo.currentText() if hasattr(self, "combo_escopo") else "Global"
        theme_mode = self.combo_tema.currentText().lower() if hasattr(self, "combo_tema") else self.tema_atual

        try:
            if not self.theme_controller:
                raise RuntimeError("Controle de tema não disponível")
            tid = self.theme_controller.create(
                name=name.strip(),
                scope=scope,
                theme_mode=theme_mode,
                cor_fundo=self.cor_fundo,
                cor_destaque=self.cor_destaque,
                imagem_fundo=self.imagem_fundo,
                imagem_opacity=float(self.imagem_opacity or 0.8),
                set_active=True,
            )
            rec = self.theme_controller.get(tid)
            if rec:
                self._apply_theme_record_to_state(rec)
            self._reload_temas_salvos()
            QMessageBox.information(self, "Tema salvo", f"Tema '{name}' salvo e definido como ativo (id={tid}).")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Erro ao salvar tema", f"Não foi possível salvar o tema: {e}")

    def _on_definir_ativo(self):
        tid = self._get_selected_tema_id()
        if not tid:
            QMessageBox.warning(self, "Selecionar tema", "Selecione um tema salvo primeiro.")
            return

        try:
            if not self.theme_controller:
                raise RuntimeError("Controle de tema indisponível")
            self.theme_controller.set_active(tid)
            rec = self.theme_controller.get(tid)
            if rec:
                self._apply_theme_record_to_state(rec)
            self._reload_temas_salvos()
            QMessageBox.information(self, "Ativo", "Tema definido como ativo.")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Não foi possível definir ativo: {e}")

    def _on_tema_salvo_selecionado(self, idx):
        tid = self._get_selected_tema_id()
        if not tid or not self.theme_controller:
            return
        try:
            rec = self.theme_controller.get(tid)
            if rec:
                self._apply_theme_record_to_state(rec)
        except Exception:
            traceback.print_exc()

    def _on_apagar_tema(self):
        tid = self._get_selected_tema_id()
        if not tid:
            QMessageBox.warning(self, "Selecionar", "Selecione um tema para apagar.")
            return

        try:
            rec = self.theme_controller.get(tid) if self.theme_controller else None
            if not rec:
                QMessageBox.warning(self, "Erro", "Tema não encontrado.")
                return
            confirm = QMessageBox.question(self, "Apagar tema", f"Tem certeza que quer apagar '{rec['name']}'?")
            if confirm != QMessageBox.StandardButton.Yes:
                return
            self.theme_controller.delete(tid)
            self._reload_temas_salvos()
            QMessageBox.information(self, "Apagado", f"Tema '{rec['name']}' apagado.")
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", "Falha ao apagar tema.")

    def _on_editar_nome_tema(self):
        tid = self._get_selected_tema_id()
        if not tid:
            QMessageBox.warning(self, "Selecionar", "Selecione um tema para editar.")
            return

        try:
            rec = self.theme_controller.get(tid)
            if not rec:
                QMessageBox.warning(self, "Erro", "Tema não encontrado.")
                return
            new_name, ok = QInputDialog.getText(self, "Editar nome do tema", "Novo nome:", text=rec["name"])
            if not ok or not new_name.strip():
                return
            self.theme_controller.update(tid, name=new_name.strip())
            self._reload_temas_salvos()
            QMessageBox.information(self, "Editado", "Nome do tema atualizado.")
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", "Falha ao editar tema.")

    def _on_resetar_para_padrao(self):
        self.tema_atual = "dark"
        self.cor_fundo = None
        self.cor_destaque = None
        self.imagem_fundo = None
        self.imagem_opacity = 0.8
        try:
            if hasattr(self, "combo_tema"):
                self.combo_tema.setCurrentText("Dark")
            if hasattr(self, "slider_opacity"):
                self.slider_opacity.setValue(int(self.imagem_opacity * 100))
        except Exception:
            pass
        self.aplicar_estilo()
        QMessageBox.information(self, "Reset", "Configurações reiniciadas para o padrão (temporariamente).")

    def _apply_theme_record_to_state(self, rec: Dict):
        try:
            if not rec:
                return
            self._theme_state["scope"] = rec.get("scope") or "Global"
            self._theme_state["theme_mode"] = rec.get("theme_mode") or "dark"
            self._theme_state["cor_fundo"] = rec.get("cor_fundo")
            self._theme_state["cor_destaque"] = rec.get("cor_destaque")
            self._theme_state["imagem_fundo"] = rec.get("imagem_fundo")
            try:
                self._theme_state["imagem_opacity"] = float(rec.get("imagem_opacity") or 0.8)
            except Exception:
                self._theme_state["imagem_opacity"] = 0.8

            try:
                if hasattr(self, "combo_tema"):
                    self.combo_tema.setCurrentText(self._theme_state["theme_mode"].capitalize())
                if hasattr(self, "slider_opacity"):
                    self.slider_opacity.setValue(int(self._theme_state["imagem_opacity"] * 100))
                if hasattr(self, "combo_escopo"):
                    self.combo_escopo.setCurrentText(self._theme_state["scope"])
            except Exception:
                pass

            self.cor_fundo = self._theme_state["cor_fundo"]
            self.cor_destaque = self._theme_state["cor_destaque"]
            self.imagem_fundo = self._theme_state["imagem_fundo"]
            self.imagem_opacity = self._theme_state["imagem_opacity"]
            self.tema_atual = self._theme_state["theme_mode"]
            self.aplicar_estilo()
        except Exception:
            traceback.print_exc()

    def aplicar_tema_padrao(self):
        self.aplicar_estilo()

    def _theme_record_from_ui(self) -> Dict:
        scope = "Global"
        if hasattr(self, "combo_escopo") and self.combo_escopo:
            try:
                scope = self.combo_escopo.currentText() or "Global"
            except Exception:
                scope = "Global"
        return {
            "scope": scope,
            "theme_mode": self.tema_atual or "dark",
            "cor_fundo": self.cor_fundo,
            "cor_destaque": self.cor_destaque,
            "imagem_fundo": self._tmp_image_path if getattr(self, "_tmp_image_path", None) else self.imagem_fundo,
            "imagem_opacity": float(self.imagem_opacity or 0.8),
        }

    def aplicar_estilo(self):
        try:
            tokens = build_theme_tokens(self._theme_record_from_ui())
            self._theme_tokens = tokens
            final_qss = build_main_qss(tokens)

            app = QApplication.instance()
            if app is not None:
                app.setStyleSheet(final_qss)
                apply_palette(app, tokens)
            else:
                self.setStyleSheet(final_qss)

            fg_qc = QColor(tokens.fg)
            accent_qc = QColor(tokens.accent)

            try:
                icon_bg = QColor(fg_qc)
                icon_bg.setAlphaF(0.08)
                for b in (getattr(self, "icon_palette", None), getattr(self, "icon_gear", None)):
                    if b:
                        try:
                            b.set_bg_color(icon_bg)
                            b.set_icon_color(accent_qc)
                        except Exception:
                            pass

                hover_bg = f"rgba({accent_qc.red()},{accent_qc.green()},{accent_qc.blue()},0.12)"
                for sec in getattr(self, "_nav_sections", []):
                    for it in getattr(sec, "items", []):
                        try:
                            it.icon_btn.set_icon_color(accent_qc)
                            if it.selected:
                                it.lbl.setStyleSheet(f"color: {accent_qc.name()};")
                                it.icon_btn.set_bg_color(QColor(accent_qc.red(), accent_qc.green(), accent_qc.blue(), 30))
                            else:
                                it.lbl.setStyleSheet(f"color: {fg_qc.name()};")
                                it.icon_btn.set_bg_color(QColor(fg_qc.red(), fg_qc.green(), fg_qc.blue(), 12))
                            it.set_hover_style(f"background: {hover_bg};")
                        except Exception:
                            pass
            except Exception:
                traceback.print_exc()

            try:
                self._refresh_profile_widget()
            except Exception:
                pass
        except Exception:
            traceback.print_exc()
            QMessageBox.warning(self, "Erro ao aplicar estilo", "Ocorreu um erro ao aplicar o tema (veja console).")

    def _apply_graphics_glow(self, accent: Optional[QColor], fg: Optional[QColor]):
        try:
            def make_effect(color, blur=14, alpha=160):
                c = QColor(color) if color is not None else QColor("#FFFFFF")
                c.setAlpha(alpha)
                eff = QGraphicsDropShadowEffect()
                eff.setBlurRadius(blur)
                eff.setColor(c)
                eff.setOffset(0, 0)
                return eff

            if getattr(self, "titulo", None):
                self.titulo.setGraphicsEffect(make_effect(accent, blur=20, alpha=200))
            if getattr(self, "main_header", None):
                self.main_header.setGraphicsEffect(make_effect(accent, blur=16, alpha=160))

            for w in (
                getattr(self, "btn_min", None),
                getattr(self, "btn_max", None),
                getattr(self, "btn_close", None),
                getattr(self, "btn_toggle_nav", None),
            ):
                if w:
                    try:
                        w.setGraphicsEffect(make_effect(fg, blur=10, alpha=140))
                    except Exception:
                        pass

            for icon_btn in (getattr(self, "icon_palette", None), getattr(self, "icon_gear", None)):
                if icon_btn:
                    try:
                        icon_btn.setGraphicsEffect(make_effect(accent, blur=14, alpha=180))
                    except Exception:
                        pass
        except Exception:
            traceback.print_exc()
