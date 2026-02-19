# banco/controles/kanban/controle_card.py
import sqlite3
import json
import os
import shutil
import tempfile
import time
import zipfile
from banco.database import conectar  # ajuste caso o módulo esteja em outro path
from contextlib import contextmanager
from typing import List, Optional, Dict, Any


class ControleCardKanban:
    """Controle avançado para cards do Kanban.

    Suporta cards hierárquicos (pai_id), anexos, checklist hierárquico (pai_id),
    tags, soft-delete via meta.arquivado, transações, export/import de pastas (ZIP) e utilitários.
    """

    IMPORT_BASE_DIR = os.path.join(os.getcwd(), "kanban_storage")

    def __init__(self, db_path: Optional[str] = None):
        # conectar() pode aceitar um path ou retornar uma conexão já configurada
        self.conn = conectar() if db_path is None else conectar(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()
        except Exception:
            # pragma pode falhar em contextos especiais; não bloqueamos a inicialização
            pass
        # garante diretório de imports
        try:
            os.makedirs(self.IMPORT_BASE_DIR, exist_ok=True)
        except Exception:
            pass

    # ------------------ utilitários ------------------
    @contextmanager
    def _transaction(self):
        try:
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def _ensure_meta_dict(self, meta: Optional[Any]) -> Dict[str, Any]:
        if meta is None:
            return {}
        if isinstance(meta, str):
            try:
                return json.loads(meta)
            except Exception:
                return {}
        if isinstance(meta, dict):
            return meta
        return {}

    def _serialize_meta(self, meta: Optional[Dict[str, Any]]) -> str:
        return json.dumps(meta or {})

    def _get_max_ordem(self, coluna_id: int, pai_id: Optional[int] = None) -> int:
        q = "SELECT COALESCE(MAX(ordem), -1) as m FROM kanban_cards WHERE coluna_id = ?"
        params = [coluna_id]
        if pai_id is None:
            q += " AND pai_id IS NULL"
        else:
            q += " AND pai_id = ?"
            params.append(pai_id)
        self.cursor.execute(q, tuple(params))
        row = self.cursor.fetchone()
        return row["m"] if row else -1

    def close(self):
        try:
            self.conn.commit()
        finally:
            self.conn.close()

    # ============================
    # CARDS
    # ============================
    def criar_card(self, coluna_id: int, titulo: str, descricao: str = "", tipo: str = "card",
                   cor_etiqueta: Optional[str] = None, pai_id: Optional[int] = None,
                   meta: Optional[Dict[str, Any]] = None, ordem: Optional[int] = None) -> Dict:
        """Cria um card. Se ordem não for fornecida, insere como último (max+1).
        Retorna o card completo (via get_card).
        """
        meta = self._ensure_meta_dict(meta)
        with self._transaction():
            if ordem is None:
                max_ordem = self._get_max_ordem(coluna_id, pai_id)
                ordem = max_ordem + 1
            self.cursor.execute(
                """
                INSERT INTO kanban_cards (coluna_id, pai_id, titulo, descricao, tipo, cor_etiqueta, ordem, meta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (coluna_id, pai_id, titulo, descricao, tipo, cor_etiqueta, ordem, self._serialize_meta(meta))
            )
            card_id = self.cursor.lastrowid
        return self.get_card(card_id)

    def get_card(self, card_id: int) -> Optional[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM kanban_cards WHERE id = ?", (card_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        card = dict(row)
        card["meta"] = self._ensure_meta_dict(card.get("meta"))
        return card

    def listar_cards(self,
                    coluna_id=None,
                    pai_id=None,
                    tags=None,
                    search=None,
                    meta_filters=None,
                    limit=None,
                    offset=None,
                    order_by="ordem ASC, criado_em ASC",
                    include_archived=False):
        """
        Lista cards com suporte a hierarquia.

        REGRAS:
        - pai_id=None → retorna SOMENTE cards de topo (pai_id IS NULL)
        - pai_id=int  → retorna apenas filhos desse card
        - inclui filtro por coluna se informado
        """

        params = []
        sql = "SELECT * FROM kanban_cards WHERE 1=1"

        # filtro por coluna
        if coluna_id is not None:
            sql += " AND coluna_id = ?"
            params.append(coluna_id)

        # 🔥 REGRA HIERÁRQUICA CORRETA
        if pai_id is None:
            sql += " AND pai_id IS NULL"
        else:
            sql += " AND pai_id = ?"
            params.append(pai_id)

        # busca textual
        if search:
            sql += " AND (titulo LIKE ? OR descricao LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        # ordenação
        if order_by:
            sql += f" ORDER BY {order_by}"

        # paginação
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                sql += " OFFSET ?"
                params.append(offset)

        try:
            self.cursor.execute(sql, tuple(params))
            rows = self.cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print("Erro ao listar cards:", e)
            return []

    def atualizar_card(self, card_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        fields = []
        values = []
        allowed = ["titulo", "descricao", "tipo", "cor_etiqueta", "pai_id", "meta", "coluna_id", "ordem"]
        for key, value in kwargs.items():
            if key in allowed:
                if key == "meta":
                    value = self._serialize_meta(self._ensure_meta_dict(value))
                fields.append(f"{key} = ?")
                values.append(value)
        if not fields:
            return None
        values.append(card_id)
        sql = f"UPDATE kanban_cards SET {', '.join(fields)}, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?"
        with self._transaction():
            self.cursor.execute(sql, tuple(values))
        return self.get_card(card_id)

    def deletar_card(self, card_id: int, hard: bool = False) -> bool:
        """Se hard=True, deleta fisicamente; caso contrário marca como arquivado no meta.
        Isso preserva o histórico e os attachments para recuperação.
        """
        if hard:
            with self._transaction():
                self.cursor.execute("DELETE FROM kanban_cards WHERE id = ?", (card_id,))
            return True

        card = self.get_card(card_id)
        if not card:
            return False
        meta = self._ensure_meta_dict(card.get("meta"))
        meta.setdefault("arquivado", True)
        with self._transaction():
            self.cursor.execute("UPDATE kanban_cards SET meta = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                                (self._serialize_meta(meta), card_id))
        return True

    # move e reordenação
    def move_card(self, card_id: int, coluna_id: int, nova_ordem: Optional[int] = None, pai_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Move card para outra coluna/pai e insere na ordem desejada (ou último).
        Ajusta ordens dos irmãos automaticamente.
        """
        card = self.get_card(card_id)
        if not card:
            return None

        with self._transaction():
            # reduzir ordens dos irmãos na coluna antiga
            self.cursor.execute(
                "UPDATE kanban_cards SET ordem = ordem - 1 WHERE coluna_id = ? AND (pai_id IS ? OR pai_id = ?) AND ordem > ?",
                (card["coluna_id"], card["pai_id"], card["pai_id"], card["ordem"]))

            # inserir no destino
            if nova_ordem is None:
                max_ord = self._get_max_ordem(coluna_id, pai_id)
                nova_ordem = max_ord + 1
            else:
                # deslocar irmãos para abrir espaço
                self.cursor.execute(
                    "UPDATE kanban_cards SET ordem = ordem + 1 WHERE coluna_id = ? AND (pai_id IS ? OR pai_id = ?) AND ordem >= ?",
                    (coluna_id, pai_id, pai_id, nova_ordem)
                )

            self.cursor.execute(
                "UPDATE kanban_cards SET coluna_id = ?, pai_id = ?, ordem = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (coluna_id, pai_id, nova_ordem, card_id)
            )
        return self.get_card(card_id)

    def reorder_cards(self, coluna_id: int, ordem_ids: List[int], pai_id: Optional[int] = None) -> bool:
        """Define a ordem de uma coluna de acordo com a lista de ids (ordem na lista = ordem no board).
        Somente cartões presentes na lista serão considerados; os demais ficam após, na ordem atual.
        """
        with self._transaction():
            for idx, cid in enumerate(ordem_ids):
                self.cursor.execute(
                    "UPDATE kanban_cards SET ordem = ?, coluna_id = ?, pai_id = ? WHERE id = ?",
                    (idx, coluna_id, pai_id, cid)
                )
        return True

    def get_card_children(self, card_id: int) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM kanban_cards WHERE pai_id = ? ORDER BY ordem ASC", (card_id,))
        rows = self.cursor.fetchall()
        result = []
        for r in rows:
            row = dict(r)
            row["meta"] = self._ensure_meta_dict(row.get("meta"))
            result.append(row)
        return result

    def get_card_tree(self, root_id: int) -> Dict[str, Any]:
        root = self.get_card(root_id)
        if not root:
            return {}
        def _walk(node):
            children = self.get_card_children(node['id'])
            node['children'] = [ _walk(child) for child in children ]
            return node
        return _walk(root)

    # ============================
    # ANEXOS
    # ============================
    def adicionar_anexo(self, card_id: int, nome_arquivo: str, caminho_local: Optional[str] = None,
                        url_remoto: Optional[str] = None, mime: Optional[str] = None, tamanho: Optional[int] = None) -> int:
        with self._transaction():
            self.cursor.execute(
                """
                INSERT INTO kanban_card_attachments (card_id, nome_arquivo, caminho_local, url_remoto, mime, tamanho)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (card_id, nome_arquivo, caminho_local, url_remoto, mime, tamanho)
            )
            return self.cursor.lastrowid

    def listar_anexos(self, card_id: int) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM kanban_card_attachments WHERE card_id = ? ORDER BY criado_em ASC", (card_id,))
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    def get_anexo(self, anexo_id: int) -> Optional[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM kanban_card_attachments WHERE id = ?", (anexo_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def deletar_anexo(self, anexo_id: int) -> bool:
        with self._transaction():
            self.cursor.execute("DELETE FROM kanban_card_attachments WHERE id = ?", (anexo_id,))
        return True

    # utilitário para copiar arquivo para área de imports e registrar no DB
    def import_file_to_folder(self, folder_card_id: int, source_file_path: str) -> Optional[int]:
        """
        Copia arquivo para a pasta física REAL do card (hierárquica)
        """
        if not os.path.isfile(source_file_path):
            raise FileNotFoundError("Arquivo não encontrado.")

        dest_dir = self._get_card_storage_path(folder_card_id)

        base = os.path.basename(source_file_path)
        timestamp = int(time.time())
        dest_name = f"{timestamp}_{base}"
        dest_path = os.path.join(dest_dir, dest_name)

        shutil.copy2(source_file_path, dest_path)
        tamanho = os.path.getsize(dest_path)

        return self.adicionar_anexo(
            folder_card_id,
            nome_arquivo=base,
            caminho_local=dest_path,
            tamanho=tamanho
        )


    # ============================
    # CHECKLIST (HIERÁRQUICO)
    # ============================
    def adicionar_checklist(self, card_id: int, descricao: str, ordem: int = 0, pai_id: Optional[int] = None) -> int:
        """Adiciona um item de checklist. Se pai_id fornecido, cria como subtarefa."""
        with self._transaction():
            self.cursor.execute(
                "INSERT INTO kanban_card_checklist (card_id, pai_id, descricao, concluido, ordem) VALUES (?, ?, ?, ?, ?)",
                (card_id, pai_id, descricao, 0, ordem)
            )
            return self.cursor.lastrowid

    def listar_checklist(self, card_id: int, parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Lista itens de checklist do card; por padrão retorna itens de topo (parent_id=None).
        Para obter subtarefas, passe parent_id=item_id."""
        if parent_id is None:
            self.cursor.execute(
                "SELECT * FROM kanban_card_checklist WHERE card_id = ? AND (pai_id IS NULL) ORDER BY ordem ASC, criado_em ASC",
                (card_id,)
            )
        else:
            self.cursor.execute(
                "SELECT * FROM kanban_card_checklist WHERE card_id = ? AND pai_id = ? ORDER BY ordem ASC, criado_em ASC",
                (card_id, parent_id)
            )
        return [dict(r) for r in self.cursor.fetchall()]

    def get_checklist_item(self, checklist_id: int) -> Optional[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM kanban_card_checklist WHERE id = ?", (checklist_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def atualizar_checklist(self, checklist_id: int, descricao: Optional[str] = None, concluido: Optional[bool] = None, ordem: Optional[int] = None, pai_id: Optional[int] = None) -> bool:
        fields = []
        values = []
        if descricao is not None:
            fields.append("descricao = ?")
            values.append(descricao)
        if concluido is not None:
            fields.append("concluido = ?")
            values.append(int(bool(concluido)))
        if ordem is not None:
            fields.append("ordem = ?")
            values.append(ordem)
        if pai_id is not None:
            fields.append("pai_id = ?")
            values.append(pai_id)
        if not fields:
            return False
        values.append(checklist_id)
        sql = f"UPDATE kanban_card_checklist SET {', '.join(fields)} WHERE id = ?"
        with self._transaction():
            self.cursor.execute(sql, tuple(values))
        return True

    def _delete_checklist_recursive(self, checklist_id: int):
        """Apaga recursivamente subtarefas (seguro se DB não tiver ON DELETE CASCADE)."""
        # obter filhos
        self.cursor.execute("SELECT id FROM kanban_card_checklist WHERE pai_id = ?", (checklist_id,))
        rows = self.cursor.fetchall()
        for r in rows:
            self._delete_checklist_recursive(r["id"])
        # apagar o próprio item
        self.cursor.execute("DELETE FROM kanban_card_checklist WHERE id = ?", (checklist_id,))

    def deletar_checklist(self, checklist_id: int) -> bool:
        with self._transaction():
            # tentamos uma deleção simples (se FK com cascade estiver presente, isso apagará filhos)
            try:
                self.cursor.execute("DELETE FROM kanban_card_checklist WHERE id = ?", (checklist_id,))
            except sqlite3.IntegrityError:
                # fallback: deletar recursivamente
                self._delete_checklist_recursive(checklist_id)
        return True

    # ============================
    # TAGS
    # ============================
    def criar_tag(self, nome: str) -> int:
        try:
            with self._transaction():
                self.cursor.execute("INSERT INTO kanban_tags (nome) VALUES (?)", (nome,))
                return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # tag já existe -> retornar id existente
            self.cursor.execute("SELECT id FROM kanban_tags WHERE nome = ?", (nome,))
            row = self.cursor.fetchone()
            return row["id"] if row else 0

    def atualizar_tag(self, tag_id: int, novo_nome: str) -> bool:
        with self._transaction():
            try:
                self.cursor.execute("UPDATE kanban_tags SET nome = ? WHERE id = ?", (novo_nome, tag_id))
                return True
            except sqlite3.IntegrityError:
                # nome já em uso
                return False

    def deletar_tag(self, tag_id: int) -> bool:
        with self._transaction():
            self.cursor.execute("DELETE FROM kanban_tags WHERE id = ?", (tag_id,))
        return True

    def adicionar_tag_ao_card(self, card_id: int, tag_id: int) -> bool:
        try:
            with self._transaction():
                self.cursor.execute("INSERT INTO kanban_card_tags (card_id, tag_id) VALUES (?, ?)", (card_id, tag_id))
                return True
        except sqlite3.IntegrityError:
            return False

    def adicionar_tag_por_nome(self, card_id: int, tag_nome: str) -> bool:
        tag_id = self.criar_tag(tag_nome)
        return self.adicionar_tag_ao_card(card_id, tag_id)

    def listar_tags_do_card(self, card_id: int) -> List[Dict[str, Any]]:
        self.cursor.execute(
            """
            SELECT t.id, t.nome
            FROM kanban_tags t
            JOIN kanban_card_tags ct ON t.id = ct.tag_id
            WHERE ct.card_id = ?
            ORDER BY t.nome ASC
            """, (card_id,)
        )
        return [dict(r) for r in self.cursor.fetchall()]

    def remover_tag_do_card(self, card_id: int, tag_id: int) -> bool:
        with self._transaction():
            self.cursor.execute("DELETE FROM kanban_card_tags WHERE card_id = ? AND tag_id = ?", (card_id, tag_id))
        return True

    # ============================
    # UTILIDADES UX / ARQUIVAMENTO
    # ============================
    def arquivar_card(self, card_id: int) -> bool:
        card = self.get_card(card_id)
        if not card:
            return False
        meta = self._ensure_meta_dict(card.get("meta"))
        meta["arquivado"] = True
        with self._transaction():
            self.cursor.execute("UPDATE kanban_cards SET meta = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                                (self._serialize_meta(meta), card_id))
        return True

    def desarquivar_card(self, card_id: int) -> bool:
        card = self.get_card(card_id)
        if not card:
            return False
        meta = self._ensure_meta_dict(card.get("meta"))
        meta.pop("arquivado", None)
        with self._transaction():
            self.cursor.execute("UPDATE kanban_cards SET meta = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                                (self._serialize_meta(meta), card_id))
        return True

    # ============================
    # EXPORT / IMPORT DE PASTAS (ZIP)
    # ============================
    def _gather_folder_structure(self, folder_card_id: int) -> Dict[str, Any]:
        """Retorna estrutura serializável (metadados) da pasta e seus filhos recursivamente, sem arquivos binários."""
        folder = self.get_card(folder_card_id) or {}
        anexos = self.listar_anexos(folder_card_id) or []
        anexos_serial = []
        for a in anexos:
            anexos_serial.append({
                'id': a.get('id'),
                'nome_arquivo': a.get('nome_arquivo'),
                'caminho_local': a.get('caminho_local'),
                'url_remoto': a.get('url_remoto'),
                'mime': a.get('mime'),
                'tamanho': a.get('tamanho')
            })
        # subfolders
        children = self.get_card_children(folder_card_id)
        subfolders = [c for c in children if c.get('tipo') == 'folder']
        return {
            'folder': {
                'id': folder.get('id'),
                'titulo': folder.get('titulo'),
                'descricao': folder.get('descricao'),
                'meta': folder.get('meta'),
                'pai_id': folder.get('pai_id'),
                'tipo': folder.get('tipo'),
                'coluna_id': folder.get('coluna_id')
            },
            'anexos': anexos_serial,
            'subfolders': [self._gather_folder_structure(f['id']) for f in subfolders]
        }

    def export_folder_as_zip(self, folder_card_id: int, zip_path: str) -> bool:
        """
        Exporta a pasta (metadados + arquivos) para um ZIP.
        O ZIP conterá:
          - folder.json (estrutura/metadata)
          - files/ (arquivos copiados, nomes únicos)
        """
        try:
            data = self._gather_folder_structure(folder_card_id)
            # temp dir
            tmpdir = tempfile.mkdtemp(prefix="kanban_export_")
            try:
                # copiar arquivos para tmpdir/files e atualizar json com nome de arquivo relativo
                files_dir = os.path.join(tmpdir, "files")
                os.makedirs(files_dir, exist_ok=True)

                def _copy_files_from_structure(struct):
                    # struct: {'folder':..., 'anexos': [...], 'subfolders': [...]}
                    for a in struct.get('anexos', []):
                        src = a.get('caminho_local')
                        if src and os.path.isfile(src):
                            # nome único no zip
                            unique_name = f"{a.get('id', int(time.time()))}_{os.path.basename(src)}"
                            dest = os.path.join(files_dir, unique_name)
                            try:
                                shutil.copy2(src, dest)
                                a['exported_filename'] = unique_name
                            except Exception:
                                a['exported_filename'] = None
                        else:
                            a['exported_filename'] = None
                    for sf in struct.get('subfolders', []):
                        _copy_files_from_structure(sf)

                _copy_files_from_structure(data)

                # escrever JSON
                json_path = os.path.join(tmpdir, "folder.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                # criar zip do tmpdir
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # adicionar json
                    zf.write(json_path, arcname="folder.json")
                    # adicionar arquivos
                    for fname in os.listdir(files_dir):
                        full = os.path.join(files_dir, fname)
                        zf.write(full, arcname=os.path.join("files", fname))
                return True
            finally:
                # limpa temp
                try:
                    shutil.rmtree(tmpdir)
                except Exception:
                    pass
        except Exception as e:
            print("Erro exportando pasta:", e)
            return False

    def import_folder_from_zip(self, parent_folder_id: int, zip_path: str) -> bool:
        """
        Importa uma pasta a partir de um ZIP gerado por export_folder_as_zip.
        parent_folder_id: card_id do folder onde a nova pasta será criada como subfolder.
        """
        if not os.path.isfile(zip_path):
            raise FileNotFoundError("ZIP não encontrado.")

        # pega coluna_id do parent para persistir nova pasta
        parent_card = self.get_card(parent_folder_id)
        coluna_id = parent_card.get('coluna_id') if parent_card else None
        if coluna_id is None:
            raise ValueError("Parent folder não tem coluna associada; import abortado.")

        tmpdir = tempfile.mkdtemp(prefix="kanban_import_")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(tmpdir)

            json_path = os.path.join(tmpdir, "folder.json")
            if not os.path.isfile(json_path):
                raise ValueError("Arquivo folder.json não encontrado no ZIP.")

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def _restore_struct(struct, target_parent_card_id):
                # struct contains 'folder', 'anexos', 'subfolders'
                title = (struct.get('folder') or {}).get('titulo') or 'Nova Pasta'
                created = self.criar_card(coluna_id=coluna_id, titulo=title, pai_id=target_parent_card_id, tipo='folder')
                if not created or not created.get('id'):
                    return None
                new_folder_id = created['id']

                # anexos: se exported_filename existir, copiar do tmpdir/files
                for a in struct.get('anexos', []):
                    exported = a.get('exported_filename')
                    if exported:
                        src = os.path.join(tmpdir, "files", exported)
                        if os.path.isfile(src):
                            # copiar para import dir permanente
                            try:
                                ts = int(time.time())
                                dest_parent = os.path.join(self.IMPORT_BASE_DIR, str(ts))
                                os.makedirs(dest_parent, exist_ok=True)
                                dest_name = f"{ts}_{os.path.basename(src)}"
                                dest_path = os.path.join(dest_parent, dest_name)
                                shutil.copy2(src, dest_path)
                                tamanho = os.path.getsize(dest_path)
                                self.adicionar_anexo(new_folder_id, nome_arquivo=a.get('nome_arquivo'), caminho_local=dest_path, tamanho=tamanho, url_remoto=a.get('url_remoto'), mime=a.get('mime'))
                            except Exception:
                                # tenta adicionar metadado sem caminho_local
                                try:
                                    self.adicionar_anexo(new_folder_id, nome_arquivo=a.get('nome_arquivo'), caminho_local=None, tamanho=a.get('tamanho'), url_remoto=a.get('url_remoto'), mime=a.get('mime'))
                                except Exception:
                                    pass
                        else:
                            # arquivo ausente no ZIP: registra apenas metadado
                            try:
                                self.adicionar_anexo(new_folder_id, nome_arquivo=a.get('nome_arquivo'), caminho_local=None, tamanho=a.get('tamanho'), url_remoto=a.get('url_remoto'), mime=a.get('mime'))
                            except Exception:
                                pass
                    else:
                        # nenhum arquivo exportado — registra metadado
                        try:
                            self.adicionar_anexo(new_folder_id, nome_arquivo=a.get('nome_arquivo'), caminho_local=None, tamanho=a.get('tamanho'), url_remoto=a.get('url_remoto'), mime=a.get('mime'))
                        except Exception:
                            pass

                # subfolders recursivos
                for sub in struct.get('subfolders', []):
                    _restore_struct(sub, new_folder_id)

                return new_folder_id

            _restore_struct(data, parent_folder_id)
            return True

        finally:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass
    
    # ==========================================================
    # DIRETÓRIO REAL POR CARD (PASTA FÍSICA HIERÁRQUICA)
    # ==========================================================

    def _get_card_storage_path(self, card_id: int) -> str:
        """
        Retorna o caminho físico da pasta de um card.
        Se for subpasta, respeita hierarquia.
        """
        card = self.get_card(card_id)
        if not card:
            raise ValueError("Card não encontrado")

        base = self.IMPORT_BASE_DIR

        # monta caminho hierárquico subindo pais
        path_parts = []
        current = card

        while current:
            safe_name = f"{current['id']}_{current['titulo'].replace('/', '_')}"
            path_parts.insert(0, safe_name)

            if not current.get("pai_id"):
                break
            current = self.get_card(current["pai_id"])

        full_path = os.path.join(base, *path_parts)
        os.makedirs(full_path, exist_ok=True)
        return full_path
    # método a adicionar na classe CardKanbanWidget
    def _open_folder(self, folder_id: int):
        """
        Abre a 'folder' representada por folder_id:
        - busca os metadados da pasta
        - lista filhos (cards) e subfolders
        - exibe um QDialog simples com a lista (duplo-clique abre subfolder)
        Ajuste visual/integração conforme sua estrutura de UI existente.
        """
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QMessageBox

        try:
            folder = self.controle.get_card(folder_id)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar pasta: {e}")
            return

        if not folder:
            QMessageBox.warning(self, "Pasta não encontrada", f"Pasta id={folder_id} não encontrada.")
            return

        children = self.controle.get_card_children(folder_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(folder.get("titulo", "Pasta"))
        layout = QVBoxLayout(dialog)

        listw = QListWidget(dialog)
        # cada item: exibe título e guarda id e tipo
        for c in children:
            title = c.get("titulo") or f"Card {c.get('id')}"
            typ = c.get("tipo") or "card"
            item = QListWidgetItem(f"[{typ}] {title}")
            # armazenar id e tipo no item para recuperar depois
            item.setData(32, {"id": c.get("id"), "tipo": typ})  # Qt.UserRole == 32
            listw.addItem(item)

        layout.addWidget(listw)

        # comportamento ao duplo-clique: abrir subfolder ou mostrar card
        def _on_item_activated(item):
            meta = item.data(32)
            if not meta:
                return
            cid = meta.get("id")
            ctype = meta.get("tipo")
            if ctype == "folder":
                # abre recursivamente outra dialog (ou poderia trocar de view principal)
                dialog.close()
                self._open_folder(cid)
            else:
                # tente abrir o card com o método existente da sua UI, se houver.
                # exemplo defensivo: se existir método _open_card ou open_card, chame-o.
                if hasattr(self, "_open_card"):
                    self._open_card(cid)
                elif hasattr(self, "open_card"):
                    self.open_card(cid)
                else:
                    # fallback: mostrar detalhes simples
                    card = self.controle.get_card(cid)
                    QMessageBox.information(self, "Card", f"#{cid}\nTítulo: {card.get('titulo')}\n\n{card.get('descricao')}")
        listw.itemActivated.connect(_on_item_activated)
        listw.itemDoubleClicked.connect(lambda it: _on_item_activated(it))

        dialog.setLayout(layout)
        dialog.resize(560, 360)
        dialog.exec_()

# fim do arquivo
