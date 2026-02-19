# banco/controles/controle_chat.py

from banco.database import conectar
from typing import List, Tuple, Optional


class ChatController:
    """
    Responsável apenas pelo fluxo do chat:
    - Criar / obter sessão
    - Salvar mensagens
    - Listar mensagens
    - Processar mensagem (encaminhar para controle_comando se necessário)
    """

    # ======================================================
    # SESSÃO
    # ======================================================

    @staticmethod
    def obter_ou_criar_sessao(usuario: str) -> int:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM chat_sessions WHERE usuario = ? ORDER BY id DESC LIMIT 1",
            (usuario,)
        )

        row = cursor.fetchone()

        if row:
            session_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO chat_sessions (usuario) VALUES (?)",
                (usuario,)
            )
            session_id = cursor.lastrowid
            conn.commit()

        conn.close()
        return session_id

    # ======================================================
    # MENSAGENS
    # ======================================================

    @staticmethod
    def salvar_mensagem(session_id: int, remetente: str, conteudo: str):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO chat_mensagens (session_id, remetente, conteudo) VALUES (?, ?, ?)",
            (session_id, remetente, conteudo)
        )

        conn.commit()
        conn.close()

    @staticmethod
    def listar_mensagens(session_id: int) -> List[Tuple]:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, remetente, conteudo, criado_em
            FROM chat_mensagens
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,)
        )

        rows = cursor.fetchall()
        conn.close()
        return rows

    # ======================================================
    # PROCESSAMENTO DA MENSAGEM
    # ======================================================

    @staticmethod
    def processar_mensagem(session_id: int, texto: str) -> str:
        """
        1. Salva mensagem do usuário
        2. Envia texto para controle_comando (se for comando)
        3. Recebe resposta
        4. Salva resposta do sistema
        """

        # salva mensagem do usuário
        ChatController.salvar_mensagem(session_id, "user", texto)

        # tenta importar controle_comando dinamicamente
        try:
            try:
                # caminho atual do projeto
                from banco.controles.chat_mestre.controle_comando import ComandoController
            except ModuleNotFoundError:
                # fallback para estruturas antigas
                from banco.controles.controle_comando import ComandoController
            resposta = ComandoController.processar_texto(texto, session_id=session_id)
        except Exception:
            # fallback caso ainda não exista controle_comando
            resposta = "Mensagem recebida e salva."

        # salva resposta do sistema
        ChatController.salvar_mensagem(session_id, "bot", resposta)

        return resposta
