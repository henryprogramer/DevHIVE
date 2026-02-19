# banco/init_db.py

from banco.auth import inicializar_tabela as init_usuarios
from banco.modelos.db_model_chat import criar_tabelas_chat
from banco.modelos.db_model_quadro import criar_tabelas_kanban
from banco.modelos.db_model_tema import criar_tabela_tema  # 👈 NOVO IMPORT

def inicializar_banco():
    """
    Inicializa todas as tabelas do sistema.
    Deve ser chamado no bootstrap do aplicativo (antes de abrir UI).
    """

    # Usuários
    init_usuarios()

    # Chat
    criar_tabelas_chat()

    # Kanban
    criar_tabelas_kanban()

    # Tema (NOVO)
    criar_tabela_tema()

    print("Banco inicializado com sucesso.")
