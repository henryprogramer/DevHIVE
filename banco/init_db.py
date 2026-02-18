# banco/init_db.py
from banco.auth import inicializar_tabela as init_usuarios
from banco.modelos.db_model_chat import criar_tabelas_chat
from banco.modelos.db_model_quadro import criar_tabelas_kanban

def inicializar_banco():
    """
    Inicializa todas as tabelas do sistema.
    Deve ser chamado no bootstrap do aplicativo (antes de abrir UI).
    """
    # Inicializa tabelas de usuários
    init_usuarios()

    # Inicializa tabelas do chat
    criar_tabelas_chat()
    criar_tabelas_kanban()

    # Futuro: chamar aqui os init dos outros módulos (kanban, dashboard...)
    # from banco.modelos.db_model_kanban import criar_tabelas_kanban
    # criar_tabelas_kanban()

    print("Banco inicializado com sucesso.")
