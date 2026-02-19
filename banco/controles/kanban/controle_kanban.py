from banco.database import conectar

class ControleKanban:
    def __init__(self):
        pass

    def listar_quadros(self, user_id):
        """Busca todos os quadros de um usuário específico."""
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, nome, cor_fundo 
                FROM quadros_kanban 
                WHERE usuario_id = ? 
                ORDER BY id DESC
            """, (user_id,))
            rows = cursor.fetchall()
            return [{"id": r[0], "nome": r[1], "cor_fundo": r[2]} for r in rows]
        except Exception as e:
            print(f"Erro ao listar: {e}")
            return []
        finally:
            conn.close()

    def criar_quadro(self, user_id, nome):
        """Insere um novo quadro no banco."""
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO quadros_kanban (usuario_id, nome) VALUES (?, ?)", (user_id, nome))
            conn.commit()
            return {"id": cursor.lastrowid, "nome": nome, "user_id": user_id}
        except Exception as e:
            print(f"Erro ao criar: {e}")
            return None
        finally:
            conn.close()

    # ==========================================
    # NOVAS LOGICAS: EDIT E DELETE
    # ==========================================

    def editar_quadro(self, quadro_id, novo_nome):
        """
        Atualiza o nome de um quadro existente.
        """
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE quadros_kanban 
                SET nome = ? 
                WHERE id = ?
            """, (novo_nome, quadro_id))
            conn.commit()
            return cursor.rowcount > 0 # Retorna True se alterou algo
        except Exception as e:
            print(f"Erro ao editar quadro {quadro_id}: {e}")
            return False
        finally:
            conn.close()

    def deletar_quadro(self, quadro_id):
        """
        Remove o quadro do banco. 
        Nota: Colunas e Cards serão removidos via CASCADE se configurado no DB.
        """
        conn = conectar()
        cursor = conn.cursor()
        try:
            # Ativa FK para garantir o Cascade se o SQLite não o fizer sozinho
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("DELETE FROM quadros_kanban WHERE id = ?", (quadro_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao deletar quadro {quadro_id}: {e}")
            return False
        finally:
            conn.close()
    
    def buscar_nome_quadro(self):
        try:
            controle = ControleKanban()
            # como você não tem get_por_id, podemos adaptar:
            quadros = controle.listar_quadros(user_id=None)  # ou criar método específico
            for q in quadros:
                if q["id"] == self.quadro_id:
                    return q["nome"]
            return "Quadro"
        except:
            return "Quadro"
