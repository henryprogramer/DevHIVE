# banco/controles/tema/controle_tema.py
"""
Controller/DAO para manipular a tabela `themes`.
Usa a função conectar() de banco.database por padrão, mas aceita uma conexão
sqlite3.Connection injetada (útil para testes ou para compartilhar a conexão global).
"""
from typing import Optional, List, Dict, Any
import sqlite3
import traceback

from banco.modelos.db_model_tema import DBModelTema
from banco.database import conectar  # função do seu projeto para obter conexão


class ControleTema:
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        """
        Se conn for None, usa conectar() e marca que 'owns' a conexão (fechará no close()).
        Se conn fornecida, não tentará fechar essa conexão no método close().
        """
        self._owns_connection = False
        if conn is None:
            # obtém conexão do projeto
            try:
                self._conn = conectar()
                self._owns_connection = True
            except Exception:
                traceback.print_exc()
                # fallback: criar conexão local mínima (não ideal, mas previne crash)
                self._conn = sqlite3.connect("data/devhive.db", check_same_thread=False)
                self._owns_connection = True
        else:
            self._conn = conn

        # garantir row_factory e criar tabela se necessário
        try:
            self._conn.row_factory = sqlite3.Row
        except Exception:
            pass

        try:
            DBModelTema.ensure_table(self._conn)
        except Exception:
            traceback.print_exc()

    def _commit(self):
        try:
            self._conn.commit()
        except Exception:
            pass

    def create(self, name: str, scope: str = "Global", theme_mode: str = "dark",
               cor_fundo: Optional[str] = None, cor_destaque: Optional[str] = None,
               imagem_fundo: Optional[str] = None, imagem_opacity: float = 0.8,
               set_active: bool = False) -> int:
        cur = self._conn.cursor()
        if set_active:
            cur.execute("UPDATE themes SET is_active = 0 WHERE is_active = 1")
        cur.execute("""
            INSERT INTO themes (name, scope, theme_mode, cor_fundo, cor_destaque, imagem_fundo, imagem_opacity, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, scope, theme_mode, cor_fundo, cor_destaque, imagem_fundo, float(imagem_opacity), 1 if set_active else 0))
        self._commit()
        return cur.lastrowid

    def update(self, theme_id: int, **fields: Any) -> None:
        if not fields:
            return
        allowed = {"name", "scope", "theme_mode", "cor_fundo", "cor_destaque", "imagem_fundo", "imagem_opacity", "is_active"}
        keys = [k for k in fields.keys() if k in allowed]
        if not keys:
            return
        set_clause = ", ".join(f"{k} = ?" for k in keys)
        params = [fields[k] for k in keys]
        sql = f"UPDATE themes SET {set_clause}, updated_at = datetime('now') WHERE id = ?"
        params.append(theme_id)
        cur = self._conn.cursor()
        cur.execute(sql, params)
        self._commit()

    def delete(self, theme_id: int) -> None:
        cur = self._conn.cursor()
        cur.execute("DELETE FROM themes WHERE id = ?", (theme_id,))
        self._commit()

    def get(self, theme_id: int) -> Optional[Dict]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM themes WHERE id = ?", (theme_id,))
        row = cur.fetchone()
        return DBModelTema.row_to_dict(row)

    def list_all(self) -> List[Dict]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM themes ORDER BY is_active DESC, created_at DESC")
        rows = cur.fetchall()
        return [DBModelTema.row_to_dict(r) for r in rows]

    def get_active(self) -> Optional[Dict]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM themes WHERE is_active = 1 LIMIT 1")
        row = cur.fetchone()
        return DBModelTema.row_to_dict(row)

    def set_active(self, theme_id: Optional[int]) -> None:
        cur = self._conn.cursor()
        cur.execute("UPDATE themes SET is_active = 0 WHERE is_active = 1")
        if theme_id is not None:
            cur.execute("UPDATE themes SET is_active = 1 WHERE id = ?", (theme_id,))
        self._commit()

    def close(self):
        """
        Fecha a conexão somente se essa instância "possui" a conexão (foi criada aqui).
        Não fecha a conexão se ela foi injetada externamente.
        """
        try:
            if self._owns_connection and self._conn:
                self._conn.close()
        except Exception:
            pass
