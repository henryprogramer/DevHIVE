import importlib
import inspect
import traceback

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QMessageBox, QWidget


class NavigationMixin:
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

    def toggle_navbar(self):
        self.navbar.setVisible(not self.navbar.isVisible())

    def clear_content_container(self):
        for i in reversed(range(self.content_layout.count())):
            w = self.content_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

    def load_shortcut_module(self, key: str):
        self.clear_content_container()
        module_candidates = []
        mapped = self.page_modules_map.get(key)
        if mapped:
            module_candidates.append(mapped)
        module_candidates.extend(
            [
                f"interface.{key}",
                f"interface.{key}_ui",
                f"interface.painel_{key}",
                f"interface.{key.replace('-', '_')}",
                f"interface.janelas.{key}",
                f"interface.janelas.painel_{key}",
                f"interface.janelas.{key.replace('-', '_')}",
            ]
        )

        loaded = False
        last_exc = None
        for module_name in module_candidates:
            try:
                mod = importlib.import_module(module_name)
                cls = None
                if hasattr(mod, "MainWidget"):
                    cls = getattr(mod, "MainWidget")
                elif hasattr(mod, "MainPage"):
                    cls = getattr(mod, "MainPage")
                else:
                    base = "".join(part.capitalize() for part in key.replace("-", "_").split("_") if part)
                    candidates = [base, "Painel" + base, base + "Widget", base + "Window", base + "Page"]
                    for cname in candidates:
                        if hasattr(mod, cname):
                            obj = getattr(mod, cname)
                            if inspect.isclass(obj):
                                cls = obj
                                break
                if cls is None:
                    for name, obj in inspect.getmembers(mod, inspect.isclass):
                        if obj.__module__ != mod.__name__:
                            continue
                        try:
                            if issubclass(obj, QWidget):
                                cls = obj
                                break
                        except Exception:
                            continue
                if cls:
                    try:
                        page_widget = cls(self.dados_usuario)
                    except TypeError:
                        page_widget = cls()
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

    def _abrir_configuracoes(self):
        QMessageBox.information(self, "Configurações", "Aba de configurações (a implementar).")
