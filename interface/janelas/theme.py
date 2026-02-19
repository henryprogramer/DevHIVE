# theme.py
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QFileDialog, QColorDialog, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from banco.controles.tema.controle_tema import ControleTema

class ThemeWindow(QWidget):
    def __init__(self, controle: Optional[ControleTema] = None, db_path: str = "data/devhive.db", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciador de Temas")
        self.controle = controle or ControleTema(db_path)
        self._build_ui()
        self._load_themes()

    def _build_ui(self):
        v = QVBoxLayout()
        self.setLayout(v)

        # listagem de temas
        v.addWidget(QLabel("Temas salvos:"))
        self.list_themes = QListWidget()
        self.list_themes.itemSelectionChanged.connect(self._on_selection_changed)
        v.addWidget(self.list_themes, 1)

        # formulário de edição / criação
        form = QVBoxLayout()

        row = QHBoxLayout()
        row.addWidget(QLabel("Nome:"))
        self.input_name = QLineEdit()
        row.addWidget(self.input_name)
        form.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Escopo:"))
        self.combo_scope = QComboBox()
        self.combo_scope.addItems(["Global", "Navbar", "Header", "Main"])
        row2.addWidget(self.combo_scope)
        row2.addWidget(QLabel("Modo:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["dark", "light"])
        row2.addWidget(self.combo_mode)
        form.addLayout(row2)

        row3 = QHBoxLayout()
        self.btn_cor_fundo = QPushButton("Cor de fundo")
        self.btn_cor_fundo.clicked.connect(self._pick_cor_fundo)
        row3.addWidget(self.btn_cor_fundo)
        self.btn_cor_destaque = QPushButton("Cor destaque")
        self.btn_cor_destaque.clicked.connect(self._pick_cor_destaque)
        row3.addWidget(self.btn_cor_destaque)
        form.addLayout(row3)

        row4 = QHBoxLayout()
        self.btn_pick_image = QPushButton("Imagem de fundo")
        self.btn_pick_image.clicked.connect(self._pick_image)
        row4.addWidget(self.btn_pick_image)
        row4.addWidget(QLabel("Opacidade:"))
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(80)
        row4.addWidget(self.slider_opacity)
        form.addLayout(row4)

        v.addLayout(form)

        # ações (Salvar / Aplicar / Editar / Apagar / Reset)
        actions = QHBoxLayout()
        self.btn_save = QPushButton("Salvar como novo (e ativar)")
        self.btn_save.clicked.connect(self._on_save_new)
        actions.addWidget(self.btn_save)

        self.btn_apply = QPushButton("Definir ativo")
        self.btn_apply.clicked.connect(self._on_set_active)
        actions.addWidget(self.btn_apply)

        self.btn_edit = QPushButton("Salvar alterações")
        self.btn_edit.clicked.connect(self._on_save_edit)
        actions.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Apagar")
        self.btn_delete.clicked.connect(self._on_delete)
        actions.addWidget(self.btn_delete)

        v.addLayout(actions)

        bottom = QHBoxLayout()
        self.btn_reload = QPushButton("Recarregar")
        self.btn_reload.clicked.connect(self._load_themes)
        bottom.addWidget(self.btn_reload)
        self.btn_reset = QPushButton("Resetar para padrão")
        self.btn_reset.clicked.connect(self._on_reset)
        bottom.addWidget(self.btn_reset)
        v.addLayout(bottom)

        # estado temporário
        self._current_theme_id = None
        self._cor_fundo = None
        self._cor_destaque = None
        self._imagem_path = None

    def _load_themes(self):
        self.list_themes.clear()
        temas = self.controle.list_all()
        for t in temas:
            label = f"{t['name']} ({t['theme_mode']})"
            if t.get("is_active"):
                label += " — ATIVO"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, t)
            self.list_themes.addItem(item)
        # limpar campos
        self._clear_form()

    def _on_selection_changed(self):
        items = self.list_themes.selectedItems()
        if not items:
            self._current_theme_id = None
            self._clear_form()
            return
        data = items[0].data(Qt.UserRole)
        self._current_theme_id = data["id"]
        self.input_name.setText(data.get("name") or "")
        self.combo_scope.setCurrentText(data.get("scope") or "Global")
        self.combo_mode.setCurrentText(data.get("theme_mode") or "dark")
        self._cor_fundo = data.get("cor_fundo")
        self._cor_destaque = data.get("cor_destaque")
        self._imagem_path = data.get("imagem_fundo")
        self.slider_opacity.setValue(int(float(data.get("imagem_opacity") or 0.8) * 100))
        self._update_color_buttons()

    def _clear_form(self):
        self.input_name.clear()
        self.combo_scope.setCurrentText("Global")
        self.combo_mode.setCurrentText("dark")
        self._cor_fundo = None
        self._cor_destaque = None
        self._imagem_path = None
        self.slider_opacity.setValue(80)
        self._update_color_buttons()

    def _update_color_buttons(self):
        if self._cor_fundo:
            self.btn_cor_fundo.setStyleSheet(f"background: {self._cor_fundo};")
        else:
            self.btn_cor_fundo.setStyleSheet("")
        if self._cor_destaque:
            self.btn_cor_destaque.setStyleSheet(f"background: {self._cor_destaque};")
        else:
            self.btn_cor_destaque.setStyleSheet("")

        if self._imagem_path:
            self.btn_pick_image.setText("Imagem: " + (self._imagem_path.split("/")[-1] or "…"))
        else:
            self.btn_pick_image.setText("Imagem de fundo")

    def _pick_cor_fundo(self):
        color = QColorDialog.getColor(QColor(self._cor_fundo) if self._cor_fundo else QColor("#ffffff"), self, "Escolher cor de fundo")
        if color.isValid():
            self._cor_fundo = color.name()
            self._update_color_buttons()

    def _pick_cor_destaque(self):
        color = QColorDialog.getColor(QColor(self._cor_destaque) if self._cor_destaque else QColor("#00aaff"), self, "Escolher cor de destaque")
        if color.isValid():
            self._cor_destaque = color.name()
            self._update_color_buttons()

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Escolher imagem de fundo", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self._imagem_path = path
            self._update_color_buttons()

    def _on_save_new(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Nome obrigatório", "Informe um nome para o tema.")
            return
        scope = self.combo_scope.currentText()
        mode = self.combo_mode.currentText()
        opacity = float(self.slider_opacity.value()) / 100.0
        # salva e define ativo
        try:
            tid = self.controle.create(name=name, scope=scope, theme_mode=mode,
                                       cor_fundo=self._cor_fundo, cor_destaque=self._cor_destaque,
                                       imagem_fundo=self._imagem_path, imagem_opacity=opacity,
                                       set_active=True)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar: {e}")
            return
        QMessageBox.information(self, "Salvo", f"Tema '{name}' salvo e definido como ativo (id={tid}).")
        self._apply_theme_to_app()

        self._load_themes()

    def _on_save_edit(self):
        if not self._current_theme_id:
            QMessageBox.warning(self, "Selecione", "Selecione um tema salvo para editar.")
            return
        fields = {
            "name": self.input_name.text().strip(),
            "scope": self.combo_scope.currentText(),
            "theme_mode": self.combo_mode.currentText(),
            "cor_fundo": self._cor_fundo,
            "cor_destaque": self._cor_destaque,
            "imagem_fundo": self._imagem_path,
            "imagem_opacity": float(self.slider_opacity.value()) / 100.0
        }
        try:
            self.controle.update(self._current_theme_id, **fields)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar alterações: {e}")
            return
        QMessageBox.information(self, "Atualizado", "Tema atualizado com sucesso.")
        self._load_themes()

    def _on_set_active(self):
        if not self._current_theme_id:
            QMessageBox.warning(self, "Selecione", "Selecione um tema para definir como ativo.")
            return
        try:
            self.controle.set_active(self._current_theme_id)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível definir ativo: {e}")
            return
        QMessageBox.information(self, "Ativo", "Tema definido como ativo.")
        self._apply_theme_to_app()

        self._load_themes()

    def _on_delete(self):
        if not self._current_theme_id:
            QMessageBox.warning(self, "Selecione", "Selecione um tema para apagar.")
            return
        rec = self.controle.get(self._current_theme_id)
        if not rec:
            QMessageBox.warning(self, "Erro", "Tema não encontrado.")
            return
        confirm = QMessageBox.question(self, "Apagar tema", f"Apagar tema '{rec['name']}'?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controle.delete(self._current_theme_id)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao apagar: {e}")
            return
        QMessageBox.information(self, "Apagado", "Tema apagado.")
        self._load_themes()

    def _on_reset(self):
        # reset local UI para padrão
        self.input_name.clear()
        self.combo_scope.setCurrentText("Global")
        self.combo_mode.setCurrentText("dark")
        self._cor_fundo = None
        self._cor_destaque = None
        self._imagem_path = None
        self.slider_opacity.setValue(80)
        self._update_color_buttons()
        QMessageBox.information(self, "Reset", "Campos resetados para o padrão (não altera temas salvos).")

    def closeEvent(self, event):
        try:
            self.controle.close()
        except Exception:
            pass
        super().closeEvent(event)
    
    def _apply_theme_to_app(self):
        theme = self.controle.get_active()
        if not theme:
            return

        app = QApplication.instance()

        mode = theme.get("theme_mode", "dark")
        bg = theme.get("cor_fundo")
        destaque = theme.get("cor_destaque") or "#00aaff"

        if not bg:
            bg = "#121212" if mode == "dark" else "#f5f5f5"

        text = "#ffffff" if mode == "dark" else "#111111"
        input_bg = "#1e1e1e" if mode == "dark" else "#ffffff"

        qss = f"""
        QWidget {{
            background-color: {bg};
            color: {text};
        }}

        QPushButton {{
            background-color: {destaque};
            color: white;
            border-radius: 6px;
            padding: 5px;
        }}

        QLineEdit, QTextEdit {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {destaque};
        }}

        QListWidget {{
            background-color: {input_bg};
            color: {text};
        }}

        QComboBox {{
            background-color: {input_bg};
            color: {text};
        }}
        """

        app.setStyleSheet(qss)

# Exemplo de execução direta (apenas para testes rápidos)
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = ThemeWindow()
    w.resize(760, 520)
    w.show()
    sys.exit(app.exec_())
