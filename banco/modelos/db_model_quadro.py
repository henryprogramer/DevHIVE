# banco/modelos/db_model_quadro.py
from banco.database import conectar

def criar_tabelas_kanban():
    """
    Cria as tabelas do módulo Kanban: Quadros, Colunas e Cards.
    """
    conn = conectar()
    cursor = conn.cursor()

    # 🔥 Ativar suporte a foreign keys no SQLite
    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. Tabela de Quadros (Onde o nome digitado no QInputDialog será salvo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quadros_kanban (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            cor_fundo TEXT DEFAULT '#f0f0f0',
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Tabela de Colunas (Ex: 'A fazer', 'Em andamento', 'Concluído')
    #cursor.execute("""
    #    CREATE TABLE IF NOT EXISTS kanban_colunas (
    #        id INTEGER PRIMARY KEY AUTOINCREMENT,
    #        quadro_id INTEGER NOT NULL,
    #        titulo TEXT NOT NULL,
    #        ordem INTEGER DEFAULT 0,
    #        FOREIGN KEY(quadro_id) REFERENCES quadros_kanban(id) ON DELETE CASCADE
    #    )
    #""")
#
    ## 3. Tabela de Cards (As tarefas propriamente ditas)
    #cursor.execute("""
    #    CREATE TABLE IF NOT EXISTS kanban_cards (
    #        id INTEGER PRIMARY KEY AUTOINCREMENT,
    #        coluna_id INTEGER NOT NULL,
    #        titulo TEXT NOT NULL,
    #        descricao TEXT,
    #        cor_etiqueta TEXT,
    #        ordem INTEGER DEFAULT 0,
    #        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    #        FOREIGN KEY(coluna_id) REFERENCES kanban_colunas(id) ON DELETE CASCADE
    #    )
    #""")

    conn.commit()
    conn.close()
    print("✅ Tabelas de Kanban verificadas/criadas com sucesso.")

def salvar_novo_quadro(user_id, nome):
    """
    Persiste o nome retornado pela interface no banco de dados.
    """
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO quadros_kanban (usuario_id, nome) VALUES (?, ?)",
            (user_id, nome)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Erro ao salvar quadro: {e}")
        return None
    finally:
        conn.close()