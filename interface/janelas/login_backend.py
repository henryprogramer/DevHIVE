import uuid
from typing import Dict, List, Optional, Tuple

MIN_NAME_LEN = 4
MIN_PASSWORD_LEN = 4

_need_funcs = [
    "criar_usuario",
    "autenticar",
    "listar_usuarios",
    "buscar_usuario_por_email",
    "buscar_usuario_por_nome",
]

base_criar_usuario = None
base_autenticar = None
base_listar_usuarios = None
base_buscar_usuario_por_email = None
base_buscar_usuario_por_nome = None

USE_FALLBACK = False

try:
    import banco.auth as _auth_mod  # type: ignore

    for fn in _need_funcs:
        if not hasattr(_auth_mod, fn):
            raise AttributeError(f"módulo 'banco.auth' não tem '{fn}'")
    base_criar_usuario = getattr(_auth_mod, "criar_usuario")
    base_autenticar = getattr(_auth_mod, "autenticar")
    base_listar_usuarios = getattr(_auth_mod, "listar_usuarios")
    base_buscar_usuario_por_email = getattr(_auth_mod, "buscar_usuario_por_email")
    base_buscar_usuario_por_nome = getattr(_auth_mod, "buscar_usuario_por_nome")
except Exception as e:
    USE_FALLBACK = True
    print("Aviso: banco.auth ausente/incompleto — usando fallback em memória para desenvolvimento.")
    print("Detalhe do erro:", e)

    _SIM_USERS: List[Dict[str, str]] = []

    def base_listar_usuarios() -> List[Dict[str, str]]:
        return list(_SIM_USERS)

    def base_buscar_usuario_por_email(email: str) -> Optional[Dict[str, str]]:
        if not email:
            return None
        for u in _SIM_USERS:
            if u.get("email", "").lower() == email.lower():
                return dict(u)
        return None

    def base_buscar_usuario_por_nome(nome: str) -> Optional[Dict[str, str]]:
        if not nome:
            return None
        for u in _SIM_USERS:
            if u.get("nome", "").lower() == nome.lower():
                return dict(u)
        return None

    def base_criar_usuario(
        nome: str,
        email: str,
        senha: str,
        cargo: Optional[str] = None,
        foto_path: Optional[str] = None,
    ) -> Tuple[bool, str]:
        if not nome or not email or not senha:
            return False, "Preencha nome, email e senha."
        if base_buscar_usuario_por_email(email):
            return False, "Já existe um usuário com esse email."
        _SIM_USERS.append(
            {
                "id": str(uuid.uuid4()),
                "nome": nome,
                "email": email,
                "senha": senha,
                "cargo": cargo,
                "foto": foto_path,
                "papel": "admin" if len(_SIM_USERS) == 0 else "membro",
                "ativo": 1,
            }
        )
        return True, "Usuário criado (fallback em memória)."

    def base_autenticar(email_or_identifier: str, senha: str) -> Tuple[bool, object]:
        u = base_buscar_usuario_por_email(email_or_identifier)
        if u and u.get("senha") == senha:
            return True, {"nome": u.get("nome"), "email": u.get("email"), "cargo": u.get("cargo"), "foto": u.get("foto")}
        u = base_buscar_usuario_por_nome(email_or_identifier)
        if u and u.get("senha") == senha:
            return True, {"nome": u.get("nome"), "email": u.get("email"), "cargo": u.get("cargo"), "foto": u.get("foto")}
        return False, "Email/nome ou senha inválidos (fallback)."


def criar_usuario(nome: str, email: str, senha: str, cargo: Optional[str] = None, foto_path: Optional[str] = None) -> Tuple[bool, str]:
    return base_criar_usuario(nome, email, senha, cargo, foto_path)  # type: ignore


def autenticar(email_or_identifier: str, senha: str) -> Tuple[bool, object]:
    return base_autenticar(email_or_identifier, senha)  # type: ignore


def listar_usuarios() -> List[Dict[str, str]]:
    return base_listar_usuarios()  # type: ignore


def buscar_usuario_por_email(email: str) -> Optional[Dict[str, str]]:
    return base_buscar_usuario_por_email(email)  # type: ignore


def buscar_usuario_por_nome(nome: str) -> Optional[Dict[str, str]]:
    return base_buscar_usuario_por_nome(nome)  # type: ignore


def validar_nome(nome: str, min_len: int = MIN_NAME_LEN) -> Tuple[bool, str]:
    if not nome or len(nome.strip()) < min_len:
        return False, f"Nome deve ter pelo menos {min_len} caracteres."
    return True, ""


def validar_senha(senha: str, min_len: int = MIN_PASSWORD_LEN) -> Tuple[bool, str]:
    if not senha or len(senha) < min_len:
        return False, f"Senha/PIN deve ter pelo menos {min_len} caracteres."
    return True, ""


def validar_email(email: str) -> Tuple[bool, str]:
    if (
        not email
        or "@" not in email
        or email.strip().startswith("@")
        or email.strip().endswith("@")
    ):
        return False, "Email inválido — deve conter '@' e formato básico correto."
    return True, ""


def seed_demo_user_if_needed() -> None:
    if not USE_FALLBACK:
        return
    try:
        if not listar_usuarios():
            criar_usuario("DevUser", "dev@example.com", "1234", cargo="Desenvolvedor", foto_path=None)
    except Exception:
        pass

