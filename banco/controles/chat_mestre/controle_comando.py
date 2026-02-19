# banco/controles/controle_comando.py

from banco.database import conectar
from typing import List, Tuple, Optional

from nucleo.comandos.chat_router import dispatch_chat_command


class ComandoController:

    # ======================================================
    # PROCESSAMENTO DO TEXTO RECEBIDO DO CHAT
    # ======================================================

    @staticmethod
    def processar_texto(texto: str, session_id: Optional[int] = None, usuario: Optional[str] = None) -> str:
        """
        Decide se o texto corresponde a um comando
        e executa ação correspondente.
        """

        texto_lower = texto.lower().strip()

        # Nova camada: comandos por palavra-chave (registry extensível)
        resultado = dispatch_chat_command(texto, session_id=session_id, usuario=usuario)
        if resultado.matched and resultado.message:
            return resultado.message

        # exemplo simples
        if texto_lower.startswith("criar comando "):
            nome = texto[15:].strip()
            ok, msg = ComandoController.criar_comando(nome)
            return msg

        if texto_lower.startswith("listar comandos"):
            comandos = ComandoController.listar_comandos()
            if not comandos:
                return "Nenhum comando cadastrado."
            return "\n".join([f"{c[0]} - {'Ativo' if c[2] else 'Arquivado'}" for c in comandos])

        # nenhum comando identificado
        return "Mensagem recebida e salva."

    # ======================================================
    # CRUD DE COMANDOS
    # ======================================================

    @staticmethod
    def criar_comando(nome: str, descricao: str = "") -> Tuple[bool, str]:
        if not nome:
            return False, "Nome do comando é obrigatório."

        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO chat_comandos (nome, descricao, ativo) VALUES (?, ?, 1)",
                (nome, descricao)
            )
            conn.commit()
            return True, "Comando criado com sucesso."
        except Exception:
            return False, "Já existe um comando com esse nome."
        finally:
            conn.close()

    @staticmethod
    def renomear_comando(nome_atual: str, novo_nome: str):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE chat_comandos SET nome = ? WHERE nome = ?",
            (novo_nome, nome_atual)
        )

        if cursor.rowcount == 0:
            conn.close()
            return False, "Comando não encontrado."

        conn.commit()
        conn.close()
        return True, "Comando renomeado."

    @staticmethod
    def arquivar_comando(nome: str):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE chat_comandos SET ativo = 0 WHERE nome = ?",
            (nome,)
        )

        if cursor.rowcount == 0:
            conn.close()
            return False, "Comando não encontrado."

        conn.commit()
        conn.close()
        return True, "Comando arquivado."

    @staticmethod
    def restaurar_comando(nome: str):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE chat_comandos SET ativo = 1 WHERE nome = ?",
            (nome,)
        )

        if cursor.rowcount == 0:
            conn.close()
            return False, "Comando não encontrado."

        conn.commit()
        conn.close()
        return True, "Comando restaurado."

    @staticmethod
    def deletar_comando(nome: str):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM chat_comandos WHERE nome = ?",
            (nome,)
        )

        if cursor.rowcount == 0:
            conn.close()
            return False, "Comando não encontrado."

        conn.commit()
        conn.close()
        return True, "Comando deletado permanentemente."

    @staticmethod
    def listar_comandos() -> List[Tuple]:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, nome, ativo FROM chat_comandos ORDER BY nome ASC"
        )

        rows = cursor.fetchall()
        conn.close()
        return rows
