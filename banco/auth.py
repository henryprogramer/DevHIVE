# banco/auth.py
import sqlite3
import uuid
import bcrypt
from datetime import datetime
from typing import Tuple, Optional, List, Dict
from banco.database import conectar
import os

# -------------------------
# Inicialização (tabelas de usuários)
# -------------------------
def inicializar_tabela():
    """
    Cria a tabela de usuários com colunas extras (foto, cargo).
    Se a tabela já existir, tenta adicionar colunas novas (migração simples).
    """
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nome_exibicao TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                papel TEXT NOT NULL,
                cargo TEXT,
                foto TEXT,
                data_criacao TEXT NOT NULL,
                ultimo_login TEXT,
                ativo INTEGER DEFAULT 1
            )
        """)
        conn.commit()

        # Migração minimalista: adiciona colunas se ausentes (robusto para upgrades)
        cursor.execute("PRAGMA table_info(usuarios)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'cargo' not in cols:
            try:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN cargo TEXT")
            except Exception:
                pass
        if 'foto' not in cols:
            try:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN foto TEXT")
            except Exception:
                pass
        conn.commit()


# garantir inicialização ao importar
try:
    inicializar_tabela()
except Exception:
    # se houver problema com DB no import, deixamos para que as funções tratem
    pass


# -------------------------
# Utilitários
# -------------------------
def existe_usuario() -> bool:
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        row = cursor.fetchone()
        return (row and row[0] > 0) if row else False


# -------------------------
# Criar usuário
# -------------------------
def criar_usuario(nome: str, email: str, senha: str, cargo: Optional[str] = None, foto_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Cria usuário. cargo e foto_path são opcionais e serão salvos no DB.
    """
    email = email.strip().lower()

    senha_hash = bcrypt.hashpw(
        senha.encode(),
        bcrypt.gensalt()
    ).decode()

    usuario_id = str(uuid.uuid4())
    data_criacao = datetime.utcnow().isoformat()

    papel = "admin" if not existe_usuario() else "membro"

    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios 
                (id, nome_exibicao, email, senha_hash, papel, cargo, foto, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario_id,
                nome.strip(),
                email,
                senha_hash,
                papel,
                cargo,
                foto_path,
                data_criacao
            ))
            conn.commit()

        return True, f"Usuário criado como {papel}."

    except sqlite3.IntegrityError:
        return False, "Email já cadastrado."


# -------------------------
# Autenticação
# -------------------------
def autenticar(email: str, senha: str) -> Tuple[bool, object]:
    email = email.strip().lower()

    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_exibicao, senha_hash, papel, cargo, foto
            FROM usuarios
            WHERE email = ? AND ativo = 1
        """, (email,))

        usuario = cursor.fetchone()

        if not usuario:
            return False, "Usuário não encontrado."

        usuario_id, nome, senha_hash, papel, cargo, foto = usuario

        if bcrypt.checkpw(senha.encode(), senha_hash.encode()):
            atualizar_ultimo_login(usuario_id)

            return True, {
                "id": usuario_id,
                "nome": nome,
                "email": email,
                "papel": papel,
                "cargo": cargo,
                "foto": foto
            }

        return False, "Senha incorreta."


# -------------------------
# Atualizar último login
# -------------------------
def atualizar_ultimo_login(usuario_id: str):
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios
            SET ultimo_login = ?
            WHERE id = ?
        """, (
            datetime.utcnow().isoformat(),
            usuario_id
        ))
        conn.commit()


# -------------------------
# Listar usuários
# -------------------------
def listar_usuarios() -> List[Dict]:
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_exibicao, email, papel, cargo, foto, ativo
            FROM usuarios
        """)
        rows = cursor.fetchall()

        usuarios = []
        for row in rows:
            usuarios.append({
                "id": row[0],
                "nome": row[1],
                "email": row[2],
                "papel": row[3],
                "cargo": row[4],
                "foto": row[5],
                "ativo": row[6]
            })

        return usuarios


# -------------------------
# Buscar por email
# -------------------------
def buscar_usuario_por_email(email: str) -> Optional[Dict]:
    email = email.strip().lower()

    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_exibicao, email, papel, cargo, foto, ativo
            FROM usuarios
            WHERE email = ?
        """, (email,))

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "nome": row[1],
            "email": row[2],
            "papel": row[3],
            "cargo": row[4],
            "foto": row[5],
            "ativo": row[6]
        }


# -------------------------
# Buscar por nome
# -------------------------
def buscar_usuario_por_nome(nome: str) -> Optional[Dict]:
    nome = nome.strip()

    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_exibicao, email, papel, cargo, foto, ativo
            FROM usuarios
            WHERE nome_exibicao = ?
        """, (nome,))

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "nome": row[1],
            "email": row[2],
            "papel": row[3],
            "cargo": row[4],
            "foto": row[5],
            "ativo": row[6]
        }
