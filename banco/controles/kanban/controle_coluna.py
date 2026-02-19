from banco.database import conectar
from typing import List, Dict, Optional

class ControleColunaKanban:
    """
    Controle para operações CRUD de colunas do Kanban.
    Cada método abre/fecha a conexão ao banco.
    """

    def __init__(self):
        pass

    def listar_colunas(self, quadro_id: Optional[int]) -> List[Dict]:
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, titulo, ordem
                FROM kanban_colunas
                WHERE quadro_id = ?
                ORDER BY ordem ASC, id ASC
            """, (quadro_id,))
            rows = cursor.fetchall()
            return [{"id": r[0], "titulo": r[1], "ordem": r[2]} for r in rows]
        except Exception as e:
            print(f"Erro ao listar colunas: {e}")
            return []
        finally:
            conn.close()

    def criar_coluna(self, quadro_id: int, titulo: str) -> Optional[Dict]:
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COALESCE(MAX(ordem), -1) + 1 
                FROM kanban_colunas
                WHERE quadro_id = ?
            """, (quadro_id,))
            proxima_ordem = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO kanban_colunas (quadro_id, titulo, ordem)
                VALUES (?, ?, ?)
            """, (quadro_id, titulo, proxima_ordem))
            conn.commit()

            return {
                "id": cursor.lastrowid,
                "titulo": titulo,
                "ordem": proxima_ordem
            }
        except Exception as e:
            print(f"Erro ao criar coluna: {e}")
            return None
        finally:
            conn.close()

    def editar_coluna(self, coluna_id: int, novo_titulo: str) -> bool:
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE kanban_colunas
                SET titulo = ?
                WHERE id = ?
            """, (novo_titulo, coluna_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao editar coluna: {e}")
            return False
        finally:
            conn.close()

    def contar_cards_na_coluna(self, coluna_id: int) -> int:
        """Retorna quantos cards (não arquivados) pertencem a esta coluna."""
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM kanban_cards WHERE coluna_id = ?", (coluna_id,))
            cnt = cursor.fetchone()[0]
            return int(cnt)
        except Exception as e:
            print(f"Erro ao contar cards na coluna {coluna_id}: {e}")
            return 0
        finally:
            conn.close()

    def deletar_coluna(self, coluna_id: int) -> bool:
        """
        Remove a coluna (cards serão removidos por cascade se FK estiver ativa).
        Retorna True se a operação afetou alguma linha.
        """
        conn = conectar()
        cursor = conn.cursor()
        try:
            # garante que o SQLite aplicará foreign keys / cascades
            try:
                cursor.execute("PRAGMA foreign_keys = ON")
            except Exception:
                pass

            cursor.execute("DELETE FROM kanban_colunas WHERE id = ?", (coluna_id,))
            conn.commit()
            affected = cursor.rowcount > 0
            if not affected:
                print(f"[ControleColuna] tentativa de deletar coluna {coluna_id} retornou rowcount=0 (não existente).")
            return affected
        except Exception as e:
            # log detalhado para ajudar debug
            print(f"Erro ao deletar coluna {coluna_id}: {e}")
            return False
        finally:
            conn.close()

    def atualizar_ordem(self, coluna_id: int, nova_ordem: int) -> bool:
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE kanban_colunas
                SET ordem = ?
                WHERE id = ?
            """, (nova_ordem, coluna_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar ordem: {e}")
            return False
        finally:
            conn.close()
