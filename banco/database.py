# banco/database.py
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
CAMINHO_DB = BASE_DIR / "dados.sqlite"

def conectar():
    """
    Conecta ao banco único do projeto.
    Retorna um sqlite3.Connection.
    """
    # garantir que o caminho exista implicitamente (sqlite cria o arquivo)
    return sqlite3.connect(str(CAMINHO_DB), timeout=30)
