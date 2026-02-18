# banco/auth.py
import sqlite3
import uuid
import bcrypt
from datetime import datetime
from typing import Tuple, Optional, List, Dict

from banco.database import conectar

# -------------------------
# Inicialização (tabelas de usuários)
# -------------------------
def inicializar_tabela():
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nome_exibicao TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                papel TEXT NOT NULL,
                data_criacao TEXT NOT NULL,
                ultimo_login TEXT,
                ativo INTEGER DEFAULT 1
            )
        """)
        conn.commit()


# -------------------------
# Utilitários
# -------------------------
def existe_usuario() -> bool:
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        return cursor.fetchone()[0] > 0


# -------------------------
# Criar usuário
# -------------------------
def criar_usuario(nome: str, email: str, senha: str) -> Tuple[bool, str]:
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
                (id, nome_exibicao, email, senha_hash, papel, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                usuario_id,
                nome.strip(),
                email,
                senha_hash,
                papel,
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
            SELECT id, nome_exibicao, senha_hash, papel
            FROM usuarios
            WHERE email = ? AND ativo = 1
        """, (email,))

        usuario = cursor.fetchone()

        if not usuario:
            return False, "Usuário não encontrado."

        usuario_id, nome, senha_hash, papel = usuario

        if bcrypt.checkpw(senha.encode(), senha_hash.encode()):
            atualizar_ultimo_login(usuario_id)

            return True, {
                "id": usuario_id,
                "nome": nome,
                "email": email,
                "papel": papel
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
            SELECT id, nome_exibicao, email, papel, ativo
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
                "ativo": row[4]
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
            SELECT id, nome_exibicao, email, papel, ativo
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
            "ativo": row[4]
        }


# -------------------------
# Buscar por nome
# -------------------------
def buscar_usuario_por_nome(nome: str) -> Optional[Dict]:
    nome = nome.strip()

    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_exibicao, email, papel, ativo
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
            "ativo": row[4]
        }
