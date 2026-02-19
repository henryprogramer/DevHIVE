# banco/modelos/db_model_tema.py
"""
Model responsável pela DDL da tabela `themes`.
Fornece método para garantir que a tabela exista em uma conexão sqlite3.
Também expõe criar_tabela_tema() para uso em banco/init_db.py.
"""
from typing import Optional
import sqlite3
import traceback

# Se desejar usar a conexão padrão para criar a tabela quando não for passado conn:
from banco.database import conectar

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'Global',
    theme_mode TEXT NOT NULL DEFAULT 'dark', -- 'dark' ou 'light'
    cor_fundo TEXT,         -- string color (hex) ou NULL
    cor_destaque TEXT,      -- string color (hex) ou NULL
    imagem_fundo TEXT,      -- path para imagem ou NULL
    imagem_opacity REAL DEFAULT 0.8,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 0
);
"""

CREATE_INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_themes_is_active ON themes(is_active);"


class DBModelTema:
    @staticmethod
    def ensure_table(conn: sqlite3.Connection) -> None:
        """
        Garante que a tabela `themes` exista na conexão fornecida.
        """
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        cur.execute(CREATE_INDEX_SQL)
        conn.commit()

    @staticmethod
    def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
        """
        Converte sqlite3.Row para dict (ou retorna None).
        """
        if row is None:
            return None
        try:
            return {k: row[k] for k in row.keys()}
        except Exception:
            # em alguns contextos row pode ser tuple; tentar mapear por descrição
            try:
                cols = [d[0] for d in row.cursor_description]
                return {cols[i]: row[i] for i in range(len(cols))}
            except Exception:
                return None


def criar_tabela_tema(conn: Optional[sqlite3.Connection] = None) -> None:
    """
    Cria a tabela themes. Se conn for None, usa banco.database.conectar() e fecha a conexão.
    """
    created = False
    if conn is None:
        try:
            conn = conectar()
            created = True
        except Exception:
            traceback.print_exc()
            # fallback: criar conexão local para não falhar completamente
            conn = sqlite3.connect("data/devhive.db", check_same_thread=False)
            created = True
    try:
        DBModelTema.ensure_table(conn)
    finally:
        if created:
            try:
                conn.close()
            except Exception:
                pass
