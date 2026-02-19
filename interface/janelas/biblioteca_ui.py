import shutil
import sqlite3
from pathlib import Path
from typing import List, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from banco.database import CAMINHO_DB


class InfoBadge(QFrame):
    def __init__(self, title: str, value: str):
        super().__init__()
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("", 10))
        layout.addWidget(lbl_title)

        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(QFont("", 13, QFont.Bold))
        layout.addWidget(self.lbl_value)

    def set_value(self, value: str):
        self.lbl_value.setText(value)


class MainWidget(QWidget):
    def __init__(self, dados_usuario=None):
        super().__init__()
        self.dados_usuario = dados_usuario or {}
        self.db_path = Path(CAMINHO_DB)
        self._build_ui()
        self._load_tree()
        self._refresh_metrics()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        title = QLabel("Biblioteca de Dados")
        title.setFont(QFont("", 16, QFont.Bold))
        root.addWidget(title)

        subtitle = QLabel("Visualizacao inicial de tabelas, volumes e amostras do banco local.")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(8)
        root.addLayout(metrics_row)

        self.badge_db_size = InfoBadge("Tamanho do banco", "--")
        self.badge_disk_free = InfoBadge("Espaco livre em disco", "--")
        self.badge_tables = InfoBadge("Tabelas encontradas", "0")
        metrics_row.addWidget(self.badge_db_size)
        metrics_row.addWidget(self.badge_disk_free)
        metrics_row.addWidget(self.badge_tables)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Estrutura", "Registros"])
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        splitter.addWidget(self.tree)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        splitter.addWidget(right_panel)

        self.preview_title = QLabel("Selecione uma tabela para visualizar")
        self.preview_title.setFont(QFont("", 12, QFont.Bold))
        right_layout.addWidget(self.preview_title)

        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectRows)
        right_layout.addWidget(self.preview_table, 1)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

    def _connect(self):
        return sqlite3.connect(str(self.db_path))

    def _refresh_metrics(self):
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        self.badge_db_size.set_value(self._format_bytes(db_size))

        usage = shutil.disk_usage(str(self.db_path.parent if self.db_path.exists() else Path.cwd()))
        self.badge_disk_free.set_value(self._format_bytes(usage.free))

        table_count = len(self._list_tables())
        self.badge_tables.set_value(str(table_count))

    def _list_tables(self) -> List[str]:
        if not self.db_path.exists():
            return []
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
            return [row[0] for row in cur.fetchall()]

    def _table_row_count(self, table_name: str) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            return int(cur.fetchone()[0])

    def _load_tree(self):
        self.tree.clear()
        if not self.db_path.exists():
            root = QTreeWidgetItem(["Banco não encontrado", "0"])
            self.tree.addTopLevelItem(root)
            return

        db_item = QTreeWidgetItem([self.db_path.name, ""])
        db_item.setExpanded(True)
        self.tree.addTopLevelItem(db_item)

        tables_root = QTreeWidgetItem(["Tabelas", ""])
        tables_root.setExpanded(True)
        db_item.addChild(tables_root)

        for table_name in self._list_tables():
            count = self._table_row_count(table_name)
            child = QTreeWidgetItem([table_name, str(count)])
            child.setData(0, Qt.UserRole, table_name)
            tables_root.addChild(child)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem):
        table_name = item.data(0, Qt.UserRole)
        if not table_name:
            return
        self._load_table_preview(str(table_name))

    def _load_table_preview(self, table_name: str):
        self.preview_title.setText(f"Tabela: {table_name} (amostra de 50 linhas)")
        columns, rows = self._fetch_preview(table_name, limit=50)

        self.preview_table.clear()
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setRowCount(len(rows))
        self.preview_table.setHorizontalHeaderLabels(columns)

        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem("" if value is None else str(value))
                self.preview_table.setItem(row_idx, col_idx, item)
        self.preview_table.resizeColumnsToContents()

    def _fetch_preview(self, table_name: str, limit: int = 50) -> Tuple[List[str], List[Tuple]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(f'PRAGMA table_info("{table_name}")')
            columns = [row[1] for row in cur.fetchall()]
            cur.execute(f'SELECT * FROM "{table_name}" LIMIT ?', (limit,))
            rows = cur.fetchall()
            return columns, rows

    @staticmethod
    def _format_bytes(size: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)
        unit = 0
        while value >= 1024 and unit < len(units) - 1:
            value /= 1024
            unit += 1
        return f"{value:.2f} {units[unit]}"

