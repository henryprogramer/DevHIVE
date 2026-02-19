# interface/objeto/card_kanban.py
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QInputDialog, QMessageBox, QSizePolicy, QTextEdit, QFileDialog,
    QDialog, QListWidget, QListWidgetItem, QScrollArea, QWidget,
    QCheckBox, QLineEdit
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QPixmap
from banco.controles.kanban.controle_card import ControleCardKanban
import json
import os
import traceback  # coloque no topo do arquivo (se já não existir)


class CardKanbanWidget(QFrame):
    """
    Widget visual de um card dentro de uma coluna Kanban.
    Integração total com ControleCardKanban.
    Agora suporta checklist hierárquico (subtarefas como linhas na tabela).
    """

    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}

    def __init__(self, card_id=None, titulo="Novo Card", coluna_id=None, parent_coluna=None):
        super().__init__(parent_coluna)
        self.setObjectName("kanbanCard")
        self.card_id = card_id
        self.coluna_id = coluna_id
        self.parent_coluna = parent_coluna
        self.controle_card = None
        self.titulo = titulo
        self.descricao = ""
        self.tipo = "card"
        self.cor_etiqueta = None
        self.meta = {}
        self.pai_id = None

        # Layout e aparência
        self.setStyleSheet("""
            QFrame#kanbanCard {
                background-color: rgba(255,255,255,0.05);
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,0.14);
            }
            QLabel#tagLabel { font-weight: bold; padding:4px 8px; border-radius:4px; background: rgba(100,100,255,0.15); }
        """)
        # largura controlada (não expandir infinitamente)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(6)

        # Tags (exibidas acima do cartão)
        self.tags_container = QHBoxLayout()
        self.layout.addLayout(self.tags_container)

        # Header
        self._init_header()

        # Descrição
        self.label_descricao = QLabel("(sem descrição)")
        self.label_descricao.setStyleSheet("font-size: 12px;")
        self.label_descricao.setWordWrap(True)
        self.layout.addWidget(self.label_descricao)

        # Toolbar para criar itens no card
        self._init_toolbar()

        # Área de seções (fundo para cada tipo de atributo)
        self.sections_container = QVBoxLayout()
        self.layout.addLayout(self.sections_container)

        # Inicializa ControleCardKanban
        self._init_controle_card()

        # Se não houver card_id mas houver coluna_id, cria um card no DB
        if not self.card_id and self.coluna_id is not None and self.controle_card:
            try:
                created = self.controle_card.criar_card(coluna_id=self.coluna_id, titulo=self.titulo, pai_id=self.pai_id)
                if created and created.get("id"):
                    self.card_id = created["id"]
            except Exception as e:
                print("Erro ao criar card inicial:", e)

        if self.card_id:
            self.load_card_data()

    # ------------------------
    # HEADER
    # ------------------------
    def _init_header(self):
        header = QHBoxLayout()
        self.label_titulo = QLabel(self.titulo)
        self.label_titulo.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.label_titulo.setWordWrap(True)
        header.addWidget(self.label_titulo)
        header.addStretch()

        self.btn_view = QPushButton("👁️")
        self.btn_view.setFixedSize(26, 26)
        self.btn_view.setCursor(Qt.PointingHandCursor)
        self.btn_view.setToolTip("Visualizar card")
        self.btn_view.clicked.connect(self.view_card)

        self.btn_edit = QPushButton("✏️")
        self.btn_edit.setFixedSize(26, 26)
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        self.btn_edit.setToolTip("Editar card")
        self.btn_edit.clicked.connect(self.editar_card)

        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(26, 26)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setToolTip("Excluir card")
        self.btn_delete.clicked.connect(self._on_delete_card)


        header.addWidget(self.btn_view)
        header.addWidget(self.btn_edit)
        header.addWidget(self.btn_delete)
        self.layout.addLayout(header)

    # ------------------------
    # TOOLBAR
    # ------------------------
    def _init_toolbar(self):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        # Botões de ação
        btn_tasks = QPushButton("✅ Tarefas")
        btn_tasks.setCursor(Qt.PointingHandCursor)
        btn_tasks.clicked.connect(lambda: self._ensure_section_and_add('checklist'))
        toolbar.addWidget(btn_tasks)

        btn_anexo = QPushButton("📎 Anexo")
        btn_anexo.setCursor(Qt.PointingHandCursor)
        btn_anexo.clicked.connect(lambda: self._ensure_section_and_add('anexo'))
        toolbar.addWidget(btn_anexo)

        btn_folder = QPushButton("📁 Pasta")
        btn_folder.setCursor(Qt.PointingHandCursor)
        btn_folder.clicked.connect(lambda: self._ensure_section_and_add('folder'))
        toolbar.addWidget(btn_folder)

        btn_tag = QPushButton("🏷️ Tag")
        btn_tag.setCursor(Qt.PointingHandCursor)
        btn_tag.clicked.connect(self.adicionar_tag)
        toolbar.addWidget(btn_tag)

        self.layout.addLayout(toolbar)

    # ------------------------
    # CONTROLE
    # ------------------------
    def _init_controle_card(self):
        try:
            # tenta achar uma instância existente em widgets ancestors (por ex. coluna/root)
            root = self.parent_coluna
            while root:
                if hasattr(root, "controle_card") and getattr(root, "controle_card"):
                    self.controle_card = root.controle_card
                    break
                root = root.parentWidget() if hasattr(root, "parentWidget") else None
            if not self.controle_card:
                self.controle_card = ControleCardKanban()
        except Exception as e:
            print("Erro ao inicializar ControleCardKanban:", e)
            self.controle_card = ControleCardKanban()

    def load_card_data(self):
        if not self.card_id or not self.controle_card:
            return
        card = self.controle_card.get_card(self.card_id)
        if not card:
            return
        self.titulo = card.get("titulo", "Novo Card")
        self.label_titulo.setText(self.titulo)
        self.descricao = card.get("descricao", "")
        self.label_descricao.setText(self.descricao or "(sem descrição)")
        self.tipo = card.get("tipo", "card")
        self.cor_etiqueta = card.get("cor_etiqueta")
        self.meta = card.get("meta", {})

        # Atualiza tags e outros itens
        self.atualizar_tags()
        # Precarrega tasks/anexos/folders em atributos para uso posterior
        self._cached_checklist = self.controle_card.listar_checklist(self.card_id)
        self._cached_anexos = self.controle_card.listar_anexos(self.card_id)
        self._cached_folders = [c for c in self.controle_card.listar_cards(pai_id=self.card_id) if c.get('tipo') == 'folder']

        # Recria as seções visuais
        self._render_sections()

    # ------------------------
    # VIEW CARD (detalhada)
    # ------------------------
    def view_card(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Card: {self.titulo}")
        dialog.setModal(True)
        dialog.resize(800, 700)
        layout = QVBoxLayout(dialog)

        # Tags e título
        tags_bar = QHBoxLayout()
        tags = self.controle_card.listar_tags_do_card(self.card_id) if self.card_id else []
        for t in tags:
            lbl = QLabel(t['nome'])
            lbl.setObjectName('tagLabel')
            tags_bar.addWidget(lbl)
        tags_bar.addStretch()
        layout.addLayout(tags_bar)

        layout.addWidget(QLabel(f"<h2>{self.titulo}</h2>"))
        label_desc = QLabel(self.descricao or "(sem descrição)")
        label_desc.setWordWrap(True)
        layout.addWidget(label_desc)

        # Toolbar dentro do dialog
        toolbar = QHBoxLayout()
        btn_tasks = QPushButton("+ Tarefa")
        btn_tasks.clicked.connect(lambda: self._ensure_section_and_add('checklist', parent_dialog=dialog))
        toolbar.addWidget(btn_tasks)
        btn_anexo = QPushButton("+ Anexo")
        btn_anexo.clicked.connect(lambda: self._ensure_section_and_add('anexo', parent_dialog=dialog))
        toolbar.addWidget(btn_anexo)
        btn_folder = QPushButton("+ Pasta")
        btn_folder.clicked.connect(lambda: self._ensure_section_and_add('folder', parent_dialog=dialog))
        toolbar.addWidget(btn_folder)
        btn_tag = QPushButton("+ Tag")
        btn_tag.clicked.connect(lambda: self._ensure_section_and_add('tag', parent_dialog=dialog))
        toolbar.addWidget(btn_tag)
        layout.addLayout(toolbar)

        # Scroll area para conteúdo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.dialog_items_layout = QVBoxLayout(container)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Renderiza secões detalhadas
        self._render_dialog_sections()

        dialog.exec_()

    # ------------------------
    # SEÇÕES (fundo / cartãozinho) - resumo no card
    # ------------------------
    def _render_sections(self):
        # Limpa sections_container
        for i in reversed(range(self.sections_container.count())):
            item = self.sections_container.itemAt(i)
            widget = item.widget() if hasattr(item, 'widget') else None
            if widget:
                widget.setParent(None)

        # Tarefas (compact)
        if getattr(self, "_cached_checklist", None):
            sec = self._build_section_frame('Tarefas', 'checklist')
            for it in self._cached_checklist:
                display_text = f"{'✅ ' if it.get('concluido') else '⬜ '}{it.get('descricao')}"
                label = QLabel(display_text)
                label.setStyleSheet('font-style: italic;')
                sec['layout'].addWidget(label)
            self.sections_container.addWidget(sec['frame'])

        # Pastas (compact)
        if getattr(self, "_cached_folders", None):
            sec = self._build_section_frame('Pastas', 'folder')
            for f in self._cached_folders:
                lbl = QLabel(f.get('titulo'))
                lbl.setStyleSheet('font-weight: bold;')
                sec['layout'].addWidget(lbl)
            self.sections_container.addWidget(sec['frame'])

        # Anexos (compact)
        if getattr(self, "_cached_anexos", None):
            sec = self._build_section_frame('Anexos', 'anexo')
            for a in self._cached_anexos:
                name = a.get('nome_arquivo')
                caminho = a.get('caminho_local')
                if caminho and self._is_image_path(caminho):
                    try:
                        pm = QPixmap(caminho).scaledToWidth(80)
                        pic = QLabel()
                        pic.setPixmap(pm)
                        sec['layout'].addWidget(pic)
                    except Exception:
                        sec['layout'].addWidget(QLabel(name))
                else:
                    sec['layout'].addWidget(QLabel(name))
            self.sections_container.addWidget(sec['frame'])

    def _build_section_frame(self, title, key):
        frame = QFrame()
        frame.setStyleSheet('background-color: rgba(255,255,255,0.06); border-radius:6px; padding:6px;')
        v = QVBoxLayout(frame)
        h = QHBoxLayout()
        h.addWidget(QLabel(f"<b>{title}</b>"))
        h.addStretch()
        btn_add = QPushButton('+')
        btn_add.setFixedSize(22, 22)
        btn_add.clicked.connect(lambda: self._ensure_section_and_add(key))
        h.addWidget(btn_add)
        v.addLayout(h)
        return {'frame': frame, 'layout': v}

    def _is_image_path(self, path):
        if not path:
            return False
        ext = os.path.splitext(path)[1].lower()
        return ext in self.IMAGE_EXTS

    # ------------------------
    # Ações de criação/adição (pasta, anexo, tarefa)
    # ------------------------
    def _ensure_section_and_add(self, section_type, parent_dialog=None):
        if not self.card_id:
            QMessageBox.warning(self, 'Erro', 'Card ainda não criado no banco.')
            return

        if section_type == 'checklist':
            desc, ok = QInputDialog.getText(self, 'Nova Tarefa', 'Descrição:')
            if ok and desc.strip():
                self.controle_card.adicionar_checklist(self.card_id, desc.strip(), ordem=0, pai_id=None)
                QMessageBox.information(self, 'Tarefa', 'Tarefa adicionada.')
        elif section_type == 'anexo':
            caminho, _ = QFileDialog.getOpenFileName(self, 'Selecionar arquivo')
            if caminho:
                nome = os.path.basename(caminho)
                try:
                    tamanho = os.path.getsize(caminho)
                except Exception:
                    tamanho = None
                # copia para import dir e adiciona
                try:
                    anexo_id = self.controle_card.import_file_to_folder(self.card_id, caminho)
                    if anexo_id:
                        QMessageBox.information(self, 'Anexo', f"Arquivo '{nome}' adicionado.")
                except Exception as e:
                    QMessageBox.warning(self, 'Erro', f'Falha ao adicionar anexo: {e}')
        elif section_type == 'folder':
            titulo, ok = QInputDialog.getText(self, 'Nova Pasta', 'Nome da pasta:')
            if ok and titulo.strip():
                created = self.controle_card.criar_card(coluna_id=self.coluna_id, titulo=titulo.strip(), pai_id=self.card_id, tipo='folder')
                QMessageBox.information(self, 'Pasta', 'Pasta criada.')
                if self.parent_coluna and hasattr(self.parent_coluna, 'refresh_cards'):
                    try:
                        self.parent_coluna.refresh_cards()
                    except Exception:
                        pass
        elif section_type == 'tag':
            tag, ok = QInputDialog.getText(self, 'Nova Tag', 'Nome:')
            if ok and tag.strip():
                tag_id = self.controle_card.criar_tag(tag.strip())
                try:
                    self.controle_card.adicionar_tag_ao_card(self.card_id, tag_id)
                except Exception:
                    pass
                QMessageBox.information(self, 'Tag', 'Tag criada e associada.')

        # recarrega dados e UI
        self.load_card_data()
        if parent_dialog is not None and hasattr(self, 'dialog_items_layout'):
            self._render_dialog_sections()

    # ------------------------
    # DIALOG: renderização detalhada (com interação)
    # ------------------------
    def _render_dialog_sections(self):
        # limpa
        for i in reversed(range(self.dialog_items_layout.count())):
            w = self.dialog_items_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # ---- Tarefas (com subtarefas) ----
        checklist = self.controle_card.listar_checklist(self.card_id, parent_id=None)
        sec_frame = QFrame()
        sec_frame.setStyleSheet('background-color: rgba(255,255,255,0.06); border-radius:6px; padding:6px;')
        sec_layout = QVBoxLayout(sec_frame)
        header = QHBoxLayout()
        header.addWidget(QLabel('<b>Tarefas</b>'))
        header.addStretch()
        btn_add = QPushButton('+')
        btn_add.setFixedSize(22, 22)
        btn_add.clicked.connect(lambda: self._ensure_section_and_add('checklist', parent_dialog=True))
        header.addWidget(btn_add)
        sec_layout.addLayout(header)

        if checklist:
            for it in checklist:
                self._render_checklist_item(it, sec_layout)
        else:
            sec_layout.addWidget(QLabel('(Nenhuma tarefa)'))

        self.dialog_items_layout.addWidget(sec_frame)

        # ---- Anexos e Pastas ----
        # Construímos um único painel com search + lista mista (anexos + subpastas)
        panel = QFrame()
        panel.setStyleSheet('background-color: rgba(255,255,255,0.06); border-radius:6px; padding:8px;')
        panel_layout = QVBoxLayout(panel)

        header = QHBoxLayout()
        header.addWidget(QLabel('<b>Conteúdo da Pasta</b>'))
        header.addStretch()

        # botão importar único (arquivo) OU pasta (zip)
        btn_import = QPushButton('Importar')
        btn_import.setFixedSize(90, 28)
        btn_import.clicked.connect(lambda: self._import_dialog_for_folder(self.card_id))
        header.addWidget(btn_import)

        # exportar: gera ZIP com arquivos + metadata
        btn_export = QPushButton('Exportar')
        btn_export.setFixedSize(90, 28)
        btn_export.clicked.connect(lambda: self._export_folder_dialog(self.card_id))
        header.addWidget(btn_export)

        panel_layout.addLayout(header)

        # search
        search = QLineEdit()
        search.setPlaceholderText("Pesquisar arquivos/pastas...")
        search.textChanged.connect(lambda txt, lay=panel_layout: self._filter_panel_items(txt, lay))
        panel_layout.addWidget(search)

        # scroll area com container (onde colocamos rows)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self._folder_container_layout = QVBoxLayout(container)
        container.setLayout(self._folder_container_layout)
        scroll.setWidget(container)
        panel_layout.addWidget(scroll)

        # popula lista com anexos e subpastas
        self._populate_folder_container(self.card_id)

        self.dialog_items_layout.addWidget(panel)

    def _populate_folder_container(self, folder_card_id):
        # limpa
        for i in reversed(range(self._folder_container_layout.count())):
            w = self._folder_container_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        # Anexos
        anexos = self.controle_card.listar_anexos(folder_card_id)
        if anexos:
            self._folder_container_layout.addWidget(QLabel('<b>Anexos</b>'))
            for a in anexos:
                row = QFrame()
                row.setObjectName('folder_row')
                row.setProperty('item_name', a.get('nome_arquivo') or '')
                row.setStyleSheet('background-color: rgba(255,255,255,0.06); border-radius:4px; padding:6px;')
                row_layout = QHBoxLayout(row)
                caminho = a.get('caminho_local')
                if caminho and self._is_image_path(caminho):
                    try:
                        pm = QPixmap(caminho).scaledToWidth(120)
                        pic = QLabel()
                        pic.setPixmap(pm)
                        row_layout.addWidget(pic)
                    except Exception:
                        row_layout.addWidget(QLabel(a.get('nome_arquivo', 'arquivo')))
                else:
                    row_layout.addWidget(QLabel(a.get('nome_arquivo', 'arquivo')))
                row_layout.addStretch()
                if caminho:
                    btn_open = QPushButton('Abrir')
                    btn_open.setFixedSize(70, 26)
                    btn_open.clicked.connect(lambda checked, p=caminho: QDesktopServices.openUrl(QUrl.fromLocalFile(p)))
                    row_layout.addWidget(btn_open)
                btn_del = QPushButton('✖')
                btn_del.setFixedSize(26, 26)
                btn_del.clicked.connect(lambda checked, aid=a['id'], fid=folder_card_id: self._delete_anexo_and_refresh(aid, fid))
                row_layout.addWidget(btn_del)
                self._folder_container_layout.addWidget(row)
        else:
            self._folder_container_layout.addWidget(QLabel('(Nenhum anexo)'))

        # Subpastas
        subfolders = [c for c in self.controle_card.listar_cards(pai_id=folder_card_id) if c.get('tipo') == 'folder']
        if subfolders:
            self._folder_container_layout.addWidget(QLabel('<b>Sub-pastas</b>'))
            for f in subfolders:
                row = QFrame()
                row.setObjectName('folder_row')
                row.setProperty('item_name', f.get('titulo') or '')
                row.setStyleSheet('background-color: rgba(255,255,255,0.06); border-radius:4px; padding:6px;')
                row_layout = QHBoxLayout(row)
                lbl = QLabel(f.get('titulo'))
                row_layout.addWidget(lbl)
                row_layout.addStretch()
                btn_open = QPushButton('Abrir')
                btn_open.setFixedSize(70, 26)
                btn_open.clicked.connect(lambda checked, fid=f['id']: self._open_folder(fid))
                row_layout.addWidget(btn_open)
                btn_del = QPushButton('✖')
                btn_del.setFixedSize(26, 26)
                btn_del.clicked.connect(lambda checked, fid=f['id'], parent_id=folder_card_id: self._delete_folder_and_refresh(fid, parent_id))
                row_layout.addWidget(btn_del)
                self._folder_container_layout.addWidget(row)

    def _filter_panel_items(self, text, panel_layout):
        """Procura por widgets com propriedade 'item_name' e alterna visibilidade."""
        txt = (text or "").strip().lower()
        for i in range(self._folder_container_layout.count()):
            w = self._folder_container_layout.itemAt(i).widget()
            if not w:
                continue
            name = w.property('item_name') or ''
            if not isinstance(name, str):
                name = str(name)
            if txt == "":
                w.setVisible(True)
            else:
                w.setVisible(txt in name.lower())

    # ações auxiliares do diálogo: importar/exportar
    def _import_dialog_for_folder(self, folder_card_id):
        # escolha: Arquivo ou Pasta (ZIP)
        choice, ok = QInputDialog.getItem(self, "Importar", "Importar:", ["Arquivo (único)", "Pasta (ZIP)"], editable=False)
        if not ok:
            return
        if choice.startswith("Arquivo"):
            caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo para importar")
            if not caminho:
                return
            try:
                self.controle_card.import_file_to_folder(folder_card_id, caminho)
                QMessageBox.information(self, "Importar", "Arquivo importado com sucesso.")
                self._populate_folder_container(folder_card_id)
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Falha ao importar arquivo: {e}")
        else:
            # importar pasta (ZIP)
            caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar ZIP de pasta", filter="ZIP Files (*.zip)")
            if not caminho:
                return
            try:
                ok = self.controle_card.import_folder_from_zip(folder_card_id, caminho)
                if ok:
                    QMessageBox.information(self, "Importar", "Pasta importada com sucesso.")
                    self._populate_folder_container(folder_card_id)
                else:
                    QMessageBox.warning(self, "Importar", "Não foi possível importar a pasta.")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Falha ao importar pasta: {e}")

    def _export_folder_dialog(self, folder_card_id):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar pasta (ZIP)", filter="ZIP Files (*.zip)")
        if not path:
            return
        if not path.lower().endswith(".zip"):
            path = path + ".zip"
        try:
            ok = self.controle_card.export_folder_as_zip(folder_card_id, path)
            if ok:
                QMessageBox.information(self, "Exportar", "Pasta exportada com sucesso.")
            else:
                QMessageBox.warning(self, "Exportar", "Erro ao exportar pasta.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro exportando: {e}")

    def _delete_anexo_and_refresh(self, anexo_id, folder_id):
        resp = QMessageBox.question(self, 'Remover anexo', 'Remover anexo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        try:
            self.controle_card.deletar_anexo(anexo_id)
        except Exception as e:
            print('Erro deletando anexo:', e)
        self._populate_folder_container(folder_id)
        self.load_card_data()

    # ---------- Atualiza _delete_folder_and_refresh para usar rotina ----------
    def _delete_folder_and_refresh(self, folder_id, parent_folder_id):
        resp = QMessageBox.question(self, 'Remover pasta', 'Deseja realmente remover esta pasta e todo o conteúdo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        try:
            self._delete_recursive(folder_id)
        except Exception as e:
            print('Erro deletando pasta:', e)
            QMessageBox.warning(self, "Erro", f"Erro deletando pasta: {e}")
            return
        # atualizar UI
        try:
            self._populate_folder_container(parent_folder_id)
        except Exception:
            traceback.print_exc()
        try:
            self.load_card_data()
        except Exception:
            traceback.print_exc()
        if self.parent_coluna and hasattr(self.parent_coluna, 'refresh_cards'):
            try:
                self.parent_coluna.refresh_cards()
            except Exception:
                traceback.print_exc()

    # ------------------------
    # Checklist rendering helpers (recursivo)
    # (restante do código de checklist igual ao que você tinha)
    # ------------------------
    def _render_checklist_item(self, item_row: dict, parent_layout: QVBoxLayout, level: int = 0):
        row = QFrame()
        row.setStyleSheet('background-color: rgba(255,255,255,0.06); border-radius:4px; padding:6px;')
        row_layout = QVBoxLayout(row)
        top = QHBoxLayout()
        indent = max(0, level * 12)
        top.setContentsMargins(indent, 0, 0, 0)

        chk = QCheckBox()
        chk.setChecked(bool(item_row.get('concluido')))
        chk.clicked.connect(lambda checked, iid=item_row['id']: self._on_check_toggled(iid, checked))
        top.addWidget(chk)

        lbl = QLabel(item_row.get('descricao', ''))
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.mouseDoubleClickEvent = lambda ev, iid=item_row['id'], cur=item_row.get('descricao', ''): self._rename_checklist_item(iid, cur)
        top.addWidget(lbl)

        top.addStretch()
        btn_add_sub = QPushButton('+s')
        btn_add_sub.setToolTip('Adicionar subtarefa')
        btn_add_sub.setFixedSize(32, 22)
        btn_add_sub.clicked.connect(lambda checked, iid=item_row['id']: self._add_subtask_dialog(iid))
        top.addWidget(btn_add_sub)

        btn_del = QPushButton('✖')
        btn_del.setFixedSize(22, 22)
        btn_del.clicked.connect(lambda checked, iid=item_row['id']: self._delete_checklist_item(iid))
        top.addWidget(btn_del)

        row_layout.addLayout(top)

        subtasks = self.controle_card.listar_checklist(self.card_id, parent_id=item_row['id'])
        if subtasks:
            for st in subtasks:
                self._render_checklist_item(st, row_layout, level=level+1)

        parent_layout.addWidget(row)

    def _on_check_toggled(self, checklist_id, checked):
        try:
            self.controle_card.atualizar_checklist(checklist_id, concluido=int(bool(checked)))
        except Exception as e:
            print('Erro atualizando checklist:', e)
        self._render_dialog_sections()
        self.load_card_data()

    def _add_subtask_dialog(self, checklist_id):
        text, ok = QInputDialog.getText(self, 'Nova Subtarefa', 'Descrição:')
        if not ok or not text.strip():
            return
        try:
            self.controle_card.adicionar_checklist(self.card_id, text.strip(), ordem=0, pai_id=checklist_id)
        except Exception as e:
            print("Erro ao adicionar subtarefa:", e)
        self._render_dialog_sections()
        self.load_card_data()

    def _rename_checklist_item(self, checklist_id, current_text=''):
        novo, ok = QInputDialog.getText(self, 'Renomear tarefa', 'Nova descrição:', text=current_text)
        if ok and novo.strip():
            try:
                self.controle_card.atualizar_checklist(checklist_id, descricao=novo.strip())
            except Exception as e:
                print("Erro renomeando checklist:", e)
        self._render_dialog_sections()
        self.load_card_data()

    def _delete_checklist_item(self, checklist_id):
        resp = QMessageBox.question(self, 'Remover tarefa', 'Remover tarefa e todas subtarefas?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        try:
            self.controle_card.deletar_checklist(checklist_id)
        except Exception as e:
            print('Erro removendo checklist:', e)
        self._render_dialog_sections()
        self.load_card_data()

    # ------------------------
    # Ações de anexo / pasta (restantes já movidas acima)
    # ------------------------

    # ------------------------
    # EDITAR / DELETAR CARD
    # ------------------------
    def editar_card(self):
        if not self.controle_card or not self.card_id:
            return
        novo_titulo, ok = QInputDialog.getText(self, "Editar Card", "Título:", text=self.titulo)
        if not ok or not novo_titulo.strip():
            return
        nova_descricao, ok_desc = QInputDialog.getMultiLineText(self, "Editar Card", "Descrição:", text=self.descricao)
        if not ok_desc:
            return
        self.controle_card.atualizar_card(self.card_id, titulo=novo_titulo.strip(), descricao=nova_descricao.strip())
        self.refresh()
        QMessageBox.information(self, "Card", "Card atualizado com sucesso.")

    def deletar_card(self):
        print(f"[DEBUG] deletar_card chamado para card_id={self.card_id}, titulo='{self.titulo}'")
        QMessageBox.information(self, "DEBUG", f"handler deletar_card chamado para card_id={self.card_id}")

        if not self.controle_card or not self.card_id:
            QMessageBox.warning(self, "Excluir Card", "Controle do card ausente ou card_id inválido.")
            print("[DEBUG] controle_card ou card_id inválido - abortando.")
            return

        resp = QMessageBox.question(self, "Excluir Card", f"Deseja excluir o card '{self.titulo}'?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            print("[DEBUG] usuário cancelou exclusão.")
            return

        try:
            card_data = self.controle_card.get_card(self.card_id)
        except Exception as e:
            card_data = None
            print(f"[DEBUG] erro ao obter card antes de deletar: {e}")

        parent_id = card_data.get('pai_id') if card_data else None

        try:
            result = self.controle_card.deletar_card(self.card_id)
            print(f"[DEBUG] controle_card.deletar_card retorno: {result}")
        except Exception as e:
            print('Erro deletando card (exception):', e)
            QMessageBox.warning(self, "Erro", f"Erro ao deletar card: {e}")
            return

        if result in (False, None):
            print("[DEBUG] deletar_card retornou False/None — verifique implementação de ControleCardKanban.deletar_card")
            QMessageBox.warning(self, "Excluir Card", "A operação de exclusão não reportou sucesso. Veja logs.")
        else:
            print("[DEBUG] exclusão no banco reportada como bem sucedida.")

        try:
            parent = self.parentWidget()
            if parent is not None:
                try:
                    parent_layout = parent.layout()
                    if parent_layout is not None:
                        parent_layout.removeWidget(self)
                except Exception:
                    pass

            self.setParent(None)
            self.hide()
            self.deleteLater()
            print("[DEBUG] widget removido da UI (setParent(None)+deleteLater).")
        except Exception as e:
            print("[DEBUG] erro removendo widget da UI:", e)

        if self.parent_coluna and hasattr(self.parent_coluna, "refresh_cards"):
            try:
                self.parent_coluna.refresh_cards()
                print("[DEBUG] parent_coluna.refresh_cards() chamado")
            except Exception as e:
                print("[DEBUG] erro chamando refresh_cards():", e)
        else:
            print("[DEBUG] parent_coluna ausente ou sem refresh_cards()")

    # ------------------------
    # TOOLBAR ACTIONS (CARD WIDGET)
    # ------------------------
    def adicionar_tag(self):
        if not self.controle_card or not self.card_id:
            return
        tag, ok = QInputDialog.getText(self, "Nova Tag", "Nome da tag:")
        if ok and tag.strip():
            tag_id = self.controle_card.criar_tag(tag.strip())
            try:
                self.controle_card.adicionar_tag_ao_card(self.card_id, tag_id)
            except Exception:
                pass
            self.atualizar_tags()
            QMessageBox.information(self, "Tag", f"Tag '{tag}' adicionada ao card.")
            self.refresh()

    # ------------------------
    # HELPERS
    # ------------------------
    def atualizar_tags(self):
        # limpa a tags_container e re-popula (tags ficam acima do cartão)
        for i in reversed(range(self.tags_container.count())):
            w = self.tags_container.itemAt(i).widget()
            if w:
                w.setParent(None)
        if not self.card_id or not self.controle_card:
            return
        tags = self.controle_card.listar_tags_do_card(self.card_id)
        for t in tags:
            lbl = QLabel(t['nome'])
            lbl.setObjectName('tagLabel')
            self.tags_container.addWidget(lbl)
        self.tags_container.addStretch()

    def refresh(self):
        """Recarrega dados do card e atualiza a representação visual."""
        self.load_card_data()
        # atualiza rótulos visuais
        self.label_titulo.setText(self.titulo)
        self.label_descricao.setText(self.descricao or "(sem descrição)")
        self.atualizar_tags()
        # avisa a coluna pai (se suportar)
        if self.parent_coluna and hasattr(self.parent_coluna, "refresh_cards"):
            try:
                self.parent_coluna.refresh_cards()
            except Exception:
                pass
    # ------------------------
    # ABRIR SUBPASTA (NAVEGAÇÃO INTERNA)
    # ------------------------
    def _open_folder(self, folder_card_id):
        """
        Abre a pasta em um diálogo reutilizando a view_card, mas sem mutar o widget
        que está na coluna. Cria um CardKanbanWidget temporário e o usa para exibir
        o diálogo — ao fechar, o widget da coluna permanece intacto.
        """
        if not folder_card_id or not self.controle_card:
            return

        try:
            # criar widget temporário (não adicionar ao layout)
            temp = CardKanbanWidget(card_id=folder_card_id,
                                    titulo="",
                                    coluna_id=self.coluna_id,
                                    parent_coluna=self.parent_coluna)
            # reaproveitar referência do controle (evita nova conexão/db)
            temp.controle_card = self.controle_card
            # carregar dados do card/pasta no temp
            temp.load_card_data()
            # abrir diálogo detalhado (view_card usa dialog.exec_ internamente)
            temp.view_card()
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao abrir pasta: {e}")
        finally:
            # garantir limpeza (se o Qt não fizer imediatamente)
            try:
                temp.deleteLater()
            except Exception:
                pass
    
    # ---------- Handler público de exclusão usado pelo botão ----------
    def _on_delete_card(self):
        """
        Handler que confirma com o usuário e executa remoção recursiva,
        atualizando a UI (coluna/dialog) corretamente.
        """
        if not self.card_id:
            return

        resposta = QMessageBox.question(
            self,
            "Excluir",
            f"Deseja realmente excluir '{self.titulo}' e todo o seu conteúdo?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if resposta != QMessageBox.Yes:
            return

        try:
            self._delete_recursive(self.card_id)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao excluir: {e}")
            traceback.print_exc()
            return

        # remover widget da UI (caso esteja na coluna)
        try:
            if self.parent_coluna and hasattr(self.parent_coluna, "remove_card_widget"):
                self.parent_coluna.remove_card_widget(self)
            else:
                # tentativa genérica de remover do layout pai
                parent = self.parentWidget()
                if parent:
                    try:
                        lay = parent.layout()
                        if lay:
                            lay.removeWidget(self)
                    except Exception:
                        pass
                self.setParent(None)
                self.hide()
                self.deleteLater()
        except Exception:
            traceback.print_exc()

        # atualizar views relacionadas
        try:
            if self.parent_coluna and hasattr(self.parent_coluna, "refresh_cards"):
                self.parent_coluna.refresh_cards()
        except Exception:
            traceback.print_exc()

        # se estiver num dialog (view_card), força reload do dialog principal caso necessário
        try:
            self.load_card_data()
        except Exception:
            pass
    
    # ---------- Deleção recursiva robusta ----------
    def _delete_recursive(self, card_id):
        """
        Remove recursivamente card + filhos + checklist + anexos (arquivo físico + registro) + tags.
        No final tenta excluir fisicamente (hard=True). Se falhar, faz soft-delete.
        """
        if not card_id:
            return

        try:
            # 1) filhos (cards cuja pai_id == card_id)
            filhos = self.controle_card.listar_cards(coluna_id=self.coluna_id, pai_id=card_id)
        except Exception:
            filhos = []

        for f in filhos:
            try:
                self._delete_recursive(f["id"])
            except Exception:
                # garanta que erro em um filho não pare o processo todo
                traceback.print_exc()

        # 2) checklist do card (apagar subtarefas via API existente)
        try:
            items = self.controle_card.listar_checklist(card_id)
            for it in items:
                try:
                    self.controle_card.deletar_checklist(it['id'])
                except Exception:
                    traceback.print_exc()
        except Exception:
            traceback.print_exc()

        # 3) anexos: remover arquivo físico (se existir) e registro DB
        try:
            anexos = self.controle_card.listar_anexos(card_id)
            for a in anexos:
                try:
                    caminho = a.get('caminho_local')
                    if caminho and os.path.isfile(caminho):
                        try:
                            os.remove(caminho)
                        except Exception:
                            # não fatal — ainda tentamos remover registro
                            traceback.print_exc()
                    # remover registro do anexo
                    try:
                        self.controle_card.deletar_anexo(a['id'])
                    except Exception:
                        traceback.print_exc()
                except Exception:
                    traceback.print_exc()
        except Exception:
            traceback.print_exc()

        # 4) tags / associações
        try:
            tags = self.controle_card.listar_tags_do_card(card_id)
            for t in tags:
                try:
                    self.controle_card.remover_tag_do_card(card_id, t['id'])
                except Exception:
                    traceback.print_exc()
        except Exception:
            # se listar_tags falhar, não interrompe
            traceback.print_exc()

        # 5) deletar o próprio card (hard delete preferível)
        try:
            self.controle_card.deletar_card(card_id, hard=True)
        except Exception:
            # fallback: marcar arquivado caso hard delete falhe
            try:
                self.controle_card.deletar_card(card_id, hard=False)
            except Exception:
                traceback.print_exc()

# fim do arquivo
