# banco/modelos/db_model_chat.py
from banco.database import conectar

def criar_tabelas_chat():
    """
    Cria as tabelas do módulo de chat dentro do mesmo banco.
    """
    conn = conectar()
    cursor = conn.cursor()

    # 🔥 Ativar suporte a foreign keys no SQLite
    cursor.execute("PRAGMA foreign_keys = ON")

    # Sessões
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Mensagens
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            remetente TEXT CHECK(remetente IN ('user','bot')),
            conteudo TEXT NOT NULL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        )
    """)

    # Comandos cadastrados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_comandos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            ativo INTEGER DEFAULT 1
        )
    """)

    # Controles (plugins / abas dinâmicas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_controls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            module_path TEXT NOT NULL,
            class_name TEXT NOT NULL,
            titulo TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()
