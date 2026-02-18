# interface/janelas/tela_login.py
from typing import Tuple, Optional, Dict, List
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QFrame, QApplication,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QSize, QRect
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon, QPainter, QPen, QBrush, QPalette
import sys
import os
import traceback

# -----------------------
# Configuráveis / Consts
# -----------------------
MIN_NAME_LEN = 4
MIN_PASSWORD_LEN = 4

# --------------------------
# IMPORT DO BACKEND (REAL) (ou fallback)
# --------------------------
# Esperado: banco/auth.py com as funções
# criar_usuario(nome, email, senha) -> (bool, mensagem)
# autenticar(email_or_identifier, senha) -> (bool, dict_or_mensagem)
# listar_usuarios() -> list[dict]
# buscar_usuario_por_email(email) -> dict | None
# buscar_usuario_por_nome(nome) -> dict | None

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

_use_fallback = False
try:
    import banco.auth as _auth_mod  # type: ignore
    # verify functions exist
    for fn in _need_funcs:
        if not hasattr(_auth_mod, fn):
            raise AttributeError(f"módulo 'banco.auth' não tem '{fn}'")
    base_criar_usuario = getattr(_auth_mod, "criar_usuario")
    base_autenticar = getattr(_auth_mod, "autenticar")
    base_listar_usuarios = getattr(_auth_mod, "listar_usuarios")
    base_buscar_usuario_por_email = getattr(_auth_mod, "buscar_usuario_por_email")
    base_buscar_usuario_por_nome = getattr(_auth_mod, "buscar_usuario_por_nome")
except Exception as e:
    # fallback in-memory implementation (útil para dev)
    _use_fallback = True
    print("Aviso: banco.auth ausente/incompleto — usando fallback em memória para desenvolvimento.")
    print("Detalhe do erro:", e)
    # traceback.print_exc()

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

    def base_criar_usuario(nome: str, email: str, senha: str) -> Tuple[bool, str]:
        if not nome or not email or not senha:
            return False, "Preencha nome, email e senha."
        if base_buscar_usuario_por_email(email):
            return False, "Já existe um usuário com esse email."
        _SIM_USERS.append({"nome": nome, "email": email, "senha": senha})
        return True, "Usuário criado (fallback em memória)."

    def base_autenticar(email_or_identifier: str, senha: str) -> Tuple[bool, object]:
        # tenta por email
        u = base_buscar_usuario_por_email(email_or_identifier)
        if u and u.get("senha") == senha:
            return True, {"nome": u.get("nome"), "email": u.get("email")}
        # tenta por nome
        u = base_buscar_usuario_por_nome(email_or_identifier)
        if u and u.get("senha") == senha:
            return True, {"nome": u.get("nome"), "email": u.get("email")}
        return False, "Email/nome ou senha inválidos (fallback)."

# Wrappers simples (mantém a conveniência de nomes anteriores)
def criar_usuario(nome: str, email: str, senha: str) -> Tuple[bool, str]:
    return base_criar_usuario(nome, email, senha)  # type: ignore

def autenticar(email_or_identifier: str, senha: str) -> Tuple[bool, object]:
    return base_autenticar(email_or_identifier, senha)  # type: ignore

def listar_usuarios() -> List[Dict[str, str]]:
    return base_listar_usuarios()  # type: ignore

def buscar_usuario_por_email(email: str) -> Optional[Dict[str, str]]:
    return base_buscar_usuario_por_email(email)  # type: ignore

def buscar_usuario_por_nome(nome: str) -> Optional[Dict[str, str]]:
    return base_buscar_usuario_por_nome(nome)  # type: ignore


# --------------------------
# Validações locais
# --------------------------
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


# --- CustomLineEdit: caret próprio e Enter handling ---
class CustomLineEdit(QLineEdit):
    def __init__(self, *args, caret_width=2, caret_color=QColor(255,255,255), caret_blink_ms=500, caret_offset=3, **kwargs):
        """
        caret_offset: deslocamento horizontal (pixels) aplicado ao caret.
                      Valores negativos movem o caret para a ESQUERDA,
                      valores positivos movem para a DIREITA.
                      (ajuste fino para alinhar com fontes/proporções)
        """
        super().__init__(*args, **kwargs)
        self._caret_color = caret_color
        self._caret_width = caret_width
        self._caret_visible = True
        self._caret_offset = int(caret_offset)
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(caret_blink_ms)
        self._blink_timer.timeout.connect(self._toggle_caret)
        self._blink_timer.start()
        try:
            if hasattr(self, "setCursorWidth"):
                # escondemos o cursor nativo para desenhar o nosso
                self.setCursorWidth(0)
        except Exception:
            pass
        self.setAlignment(Qt.AlignVCenter)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_InputMethodEnabled, True)

        # repintar quando cursor/texto mudarem
        try:
            self.cursorPositionChanged.connect(lambda *a: self.update())
            self.textChanged.connect(lambda *a: self.update())
        except Exception:
            pass

    def _toggle_caret(self):
        self._caret_visible = not self._caret_visible
        try:
            cr = self.cursorRect()
            cr.adjust(-2, -2, 2, 2)
            self.update(cr)
        except Exception:
            self.update()

    def focusInEvent(self, ev):
        self._caret_visible = True
        self._blink_timer.start()
        super().focusInEvent(ev)

    def focusOutEvent(self, ev):
        self._caret_visible = False
        self._blink_timer.stop()
        super().focusOutEvent(ev)

    def keyPressEvent(self, ev):
        # Captura Enter/Return para pular campos / confirmar ação.
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter) and not (ev.modifiers() & Qt.ControlModifier):
            win = self.window()
            if hasattr(win, "handle_enter_from"):
                try:
                    win.handle_enter_from(self)
                    ev.accept()
                    return
                except Exception:
                    pass
        super().keyPressEvent(ev)

    def paintEvent(self, ev):
        """
        Desenha caret posicionado à direita do caractere anterior.
        Estratégia:
         - usar cursorRect().x quando cursorRect fornece largura consistente;
         - senão, estimar largura do caractere anterior com fontMetrics().horizontalAdvance();
         - fallback para averageCharWidth.
        """
        super().paintEvent(ev)
        if self.hasFocus() and self._caret_visible:
            try:
                cr: QRect = self.cursorRect()

                # vertical/altura do caret
                if cr.height() > 0:
                    y = cr.y()
                    h = cr.height()
                else:
                    h = self.fontMetrics().height()
                    y = max(0, (self.height() - h) // 2)

                # horizontal: tentar posicionamento mais conservador para evitar overshoot
                if cr.width() > 1:
                    # usar cr.x() (ponto base) ao invés de cr.x() + cr.width()
                    # reduz posicionamento demasiado à direita em algumas plataformas/fontes
                    x_base = cr.x()
                else:
                    cp = self.cursorPosition()
                    text = self.text() or ""
                    if cp > 0 and len(text) >= cp:
                        prev_char = text[cp-1]
                        adv = self.fontMetrics().horizontalAdvance(prev_char)
                        if adv <= 0:
                            adv = max(1, self.fontMetrics().averageCharWidth())
                        # tentar posicionar relativo ao início do texto; cursorRect().x pode ser o ponto base
                        x_base = cr.x() + adv
                    else:
                        x_base = cr.x() + max(1, self.fontMetrics().averageCharWidth())

                x = int(x_base + self._caret_offset)
                # evitar sair dos limites do widget
                x = max(0, min(x, self.width() - 1))
                w = max(1, self._caret_width)

                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                pen = QPen(self._caret_color)
                pen.setWidth(0)
                painter.setPen(pen)
                painter.setBrush(QBrush(self._caret_color))
                painter.drawRect(x, y, int(w), int(h))
                painter.end()
            except Exception:
                pass


class TelaLogin(QWidget):
    INPUT_HEIGHT = 55

    def __init__(self, ao_logar_callback):
        super().__init__()
        self.ao_logar_callback = ao_logar_callback
        self.modo_cadastro = False
        self._single_user: Optional[Dict[str, str]] = None  # dict quando houver apenas 1 usuário

        self.setWindowTitle("DevHive - Acesso")
        self.setFixedSize(840, 800)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setFixedSize(self.width() - 80, self.height() - 80)
        self.container.move(40, 40)
        self.container.setGraphicsEffect(self._criar_glow(40, QColor(255, 255, 255, 100)))

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.container_layout.setSpacing(22)
        self.container_layout.setContentsMargins(120, 40, 120, 60)

        # Caminho absoluto correto
        base_dir = os.path.dirname(os.path.dirname(__file__))
        logo_path = os.path.join(base_dir, "assets", "logo.png")

        self.logo_label = QLabel(self.container)
        self.logo_label.setAlignment(Qt.AlignCenter)

        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(
                110, 110, 
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("DevHive")
            self.logo_label.setFont(QFont("Arial", 18, QFont.Bold))
            self.logo_label.setStyleSheet("color: white;")

        self.container_layout.addWidget(self.logo_label)

        # Título
        self.label_titulo = QLabel("Login", self.container)
        self.label_titulo.setAlignment(Qt.AlignCenter)
        self.label_titulo.setFont(QFont("Arial", 28, QFont.Bold))
        self.label_titulo.setStyleSheet("color: white;")
        self.label_titulo.setGraphicsEffect(self._criar_glow(30, QColor(255, 255, 255, 200)))
        self.container_layout.addWidget(self.label_titulo)

        # single user label
        self.single_user_label = QLabel("", self.container)
        self.single_user_label.setAlignment(Qt.AlignCenter)
        self.single_user_label.setFont(QFont("Arial", 12, QFont.Normal))
        self.single_user_label.setStyleSheet("color: rgba(255,255,255,0.9);")
        self.single_user_label.hide()
        self.container_layout.addWidget(self.single_user_label)

        # INPUTS
        self.input_nome = CustomLineEdit(self.container)
        self.input_nome.setPlaceholderText("Nome de exibição")
        self.input_nome.setObjectName("input")
        self._padronizar_input(self.input_nome)
        self.input_nome.hide()
        self.container_layout.addWidget(self.input_nome)

        self.input_email = CustomLineEdit(self.container)
        self.input_email.setPlaceholderText("Email ou nome de usuário")
        self.input_email.setObjectName("input")
        self._padronizar_input(self.input_email)
        self.container_layout.addWidget(self.input_email)

        # senha
        self.password_container = QFrame(self.container)
        self.password_container.setObjectName("passwordFrame")
        self.password_container.setFixedHeight(self.INPUT_HEIGHT)

        pass_layout = QHBoxLayout(self.password_container)
        pass_layout.setContentsMargins(0, 0, 8, 0)
        pass_layout.setSpacing(0)

        self.input_senha = CustomLineEdit(self.password_container)
        self.input_senha.setPlaceholderText("Senha")
        self.input_senha.setEchoMode(QLineEdit.Password)
        self.input_senha.setObjectName("input_inner")
        self._padronizar_input(self.input_senha)
        self.input_senha.setStyleSheet("background: transparent; border: none; padding: 0px 15px; color: white;")
        pass_layout.addWidget(self.input_senha)

        self.eye_btn = QPushButton(self.password_container)
        self.eye_btn.setCursor(Qt.PointingHandCursor)
        self.eye_btn.setFixedSize(35, 30)
        self.eye_btn.setStyleSheet("background: transparent; border: none;")
        self.eye_btn.setIcon(self._criar_icone_olho(22, 16, visible=False))
        self.eye_btn.setIconSize(QSize(22, 16))
        self.eye_btn.clicked.connect(self._toggle_senha)
        pass_layout.addWidget(self.eye_btn)

        self.container_layout.addWidget(self.password_container)

        # botões
        self.botao_principal = QPushButton("Entrar", self.container)
        self.botao_principal.setObjectName("botaoPrincipal")
        self.botao_principal.setMinimumHeight(50)
        self.botao_principal.setCursor(Qt.PointingHandCursor)
        self.botao_principal.clicked.connect(self.executar_acao)
        self.container_layout.addWidget(self.botao_principal)

        self.botao_alternar = QPushButton("Criar conta", self.container)
        self.botao_alternar.setObjectName("botaoLink")
        self.botao_alternar.setCursor(Qt.PointingHandCursor)
        self.botao_alternar.clicked.connect(self.alternar_modo)
        self.container_layout.addWidget(self.botao_alternar)

        # controles da janela
        self.botao_fechar = QPushButton("X", self)
        self.botao_minimizar = QPushButton("-", self)
        for btn in (self.botao_fechar, self.botao_minimizar):
            btn.setStyleSheet("background: transparent; border: none; color: white; font-weight: bold; font-size: 18px;")
            btn.setFixedSize(35, 35)
            btn.setCursor(Qt.PointingHandCursor)
        self.botao_fechar.clicked.connect(self.close)
        self.botao_minimizar.clicked.connect(self.showMinimized)

        # splash
        self.splash_logo = QLabel(self)
        self.splash_logo.setAlignment(Qt.AlignCenter)
        splash_size = 250
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(splash_size, splash_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.splash_logo.setPixmap(pix)
        else:
            self.splash_logo.setText("DevHive")
            self.splash_logo.setFont(QFont("Arial", 48, QFont.Bold))
            self.splash_logo.setStyleSheet("color: white;")

        self.splash_logo.setGeometry((self.width() - splash_size)//2, (self.height() - splash_size)//2, splash_size, splash_size)
        self.logo_effect = QGraphicsOpacityEffect(self.splash_logo)
        self.splash_logo.setGraphicsEffect(self.logo_effect)
        self.container.hide()
        QTimer.singleShot(50, self.start_splash)

        self.aplicar_estilo()
        self._configurar_paleta_e_caret()
        self.centralizar_janela()
        self._position_window_buttons()

        # verificar usuários e ajustar UI
        QTimer.singleShot(0, self._check_single_user)

    # utilitários / helpers (todos presentes)
    def _criar_glow(self, blur, color):
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(blur)
        glow.setColor(color)
        glow.setOffset(0, 0)
        return glow

    def _criar_icone_olho(self, w, h, visible=False):
        pix = QPixmap(w, h)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(2)
        p.setPen(pen)
        p.drawEllipse(1, 1, w-2, h-2)
        if visible:
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(w//2 - 3, h//2 - 3, 6, 6)
        else:
            p.drawLine(w//2 - 4, h - 4, w//2 + 4, 4)
        p.end()
        return QIcon(pix)

    def _toggle_senha(self):
        if self.input_senha.echoMode() == QLineEdit.Password:
            self.input_senha.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setIcon(self._criar_icone_olho(22, 16, visible=True))
        else:
            self.input_senha.setEchoMode(QLineEdit.Password)
            self.eye_btn.setIcon(self._criar_icone_olho(22, 16, visible=False))

    def centralizar_janela(self):
        tela = QApplication.primaryScreen().availableGeometry()
        self.move((tela.width() - self.width()) // 2, (tela.height() - self.height()) // 2)

    def _position_window_buttons(self):
        cx, cy, cw = self.container.x(), self.container.y(), self.container.width()
        self.botao_fechar.move(cx + cw - 45, cy + 10)
        self.botao_minimizar.move(cx + cw - 85, cy + 10)

    def _padronizar_input(self, widget: CustomLineEdit):
        widget.setFixedHeight(self.INPUT_HEIGHT)
        widget.setAlignment(Qt.AlignVCenter)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        widget.setFocusPolicy(Qt.StrongFocus)
        widget.setAttribute(Qt.WA_InputMethodEnabled, True)

    def _configurar_paleta_e_caret(self):
        pal = QPalette()
        pal.setColor(QPalette.Text, QColor(255, 255, 255))
        pal.setColor(QPalette.Base, QColor(0, 0, 0, 0))
        try:
            pal.setColor(QPalette.PlaceholderText, QColor(255, 255, 255, 140))
        except Exception:
            pass
        pal.setColor(QPalette.Highlight, QColor(255, 255, 255))
        pal.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

        for widget in (self.input_nome, self.input_email, self.input_senha):
            widget.setPalette(pal)

    def aplicar_estilo(self):
        self.setStyleSheet(f"""
        QWidget {{ background-color: transparent; color: white; }}

        QFrame#container {{
            background-color: rgba(0, 0, 0, 0.85);
            border-radius: 30px;
            border: 2px solid rgba(255, 255, 255, 0.9);
        }}

        QLineEdit#input {{
            background: transparent;
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding: 0px 15px; 
            font-size: 16px;
            color: white;
            min-height: {self.INPUT_HEIGHT}px;
        }}

        QFrame#passwordFrame {{
            background: transparent;
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }}
        QFrame#passwordFrame:hover {{
            border-bottom: 1px solid white;
        }}

        QLineEdit#input:focus {{ border-bottom: 1px solid white; }}

        QPushButton#botaoPrincipal {{
            background-color: transparent;
            border: 2px solid white;
            border-radius: 25px;
            padding: 14px;
            font-weight: bold;
            font-size: 16px;
        }}
        QPushButton#botaoPrincipal:hover {{ background-color: white; color: black; }}

        QPushButton#botaoLink {{
            background: transparent;
            color: white;
            border: none;
            font-size: 14px;
        }}
        QPushButton#botaoLink:hover {{ text-decoration: underline; }}
        """)

    # animações (splash)
    def start_splash(self):
        self.blink_count = 0
        self._blink_logo()

    def _blink_logo(self):
        if self.blink_count >= 2:
            self._fade_logo()
            return
        self.blink_count += 1
        anim = QPropertyAnimation(self.logo_effect, b"opacity", self)
        anim.setDuration(250)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.finished.connect(lambda: QTimer.singleShot(150, self._blink_logo))
        anim.start()

    def _fade_logo(self):
        anim = QPropertyAnimation(self.logo_effect, b"opacity", self)
        anim.setDuration(800)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self._on_splash_finished)
        anim.start()

    def _on_splash_finished(self):
        if getattr(self, "splash_logo", None):
            self.splash_logo.hide()
        self.container.show()
        self.container.setEnabled(True)
        self.botao_fechar.raise_()
        self.botao_minimizar.raise_()

        # dá um pequeno atraso para garantir que a UI já esteja visível, então
        # define o foco inicial no campo apropriado.
        QTimer.singleShot(60, self._set_initial_focus)

    def _set_initial_focus(self):
        """
        Garante que o campo adequado receba foco quando a janela ficar visível.
        Chama _check_single_user() para assegurar que o estado de single-user esteja correto.
        """
        try:
            # atualiza estado (em caso de race com init)
            self._check_single_user()
        except Exception:
            pass

        try:
            # garante que a janela esteja ativa e visível antes de focar
            self.raise_()
            self.activateWindow()
            self.setFocus()
        except Exception:
            pass

        # prioridade de foco conforme modo/estado
        try:
            if self.modo_cadastro:
                if self.input_nome.isVisible():
                    self.input_nome.setFocus()
                    try:
                        self.input_nome.selectAll()
                    except Exception:
                        pass
                    return

            if self._single_user:
                # se há apenas 1 usuário, foca a senha
                self.input_senha.setFocus()
                try:
                    self.input_senha.selectAll()
                except Exception:
                    pass
                return

            # default: foca o campo de email (ou senha caso email não esteja visível)
            if self.input_email.isVisible():
                self.input_email.setFocus()
                try:
                    self.input_email.selectAll()
                except Exception:
                    pass
            else:
                self.input_senha.setFocus()
                try:
                    self.input_senha.selectAll()
                except Exception:
                    pass

        except Exception:
            # fallback: apenas tenta focar o botão principal
            try:
                self.botao_principal.setFocus()
            except Exception:
                pass

    def alternar_modo(self):
        self.modo_cadastro = not self.modo_cadastro
        self.label_titulo.setText("Cadastro" if self.modo_cadastro else "Login")
        self.botao_principal.setText("Cadastrar" if self.modo_cadastro else "Entrar")
        self.botao_alternar.setText("Já tenho conta" if self.modo_cadastro else "Criar conta")
        self.input_nome.setVisible(self.modo_cadastro)

        if self.modo_cadastro:
            self.input_email.show()
            self.single_user_label.hide()
        else:
            self._check_single_user()

    def _check_single_user(self):
        try:
            usuarios = listar_usuarios() or []
        except Exception:
            usuarios = []

        if len(usuarios) == 1 and not self.modo_cadastro:
            self._single_user = usuarios[0]
            self.input_email.hide()
            nome = self._single_user.get('nome') or self._single_user.get('email') or "Usuário"
            self.single_user_label.setText(f"Entrar como: <b>{nome}</b> — insira sua senha")
            self.single_user_label.show()
            self.input_senha.setPlaceholderText(f"Senha — {nome}")
        else:
            self._single_user = None
            self.input_email.show()
            self.single_user_label.hide()
            self.input_senha.setPlaceholderText("Senha")
        self.container.update()

    def _inputs_filled_for_current_mode(self) -> bool:
        """
        Verifica se os campos necessários estão válidos para acionar Entrar/Cadastrar.
        """
        if self.modo_cadastro:
            nome = self.input_nome.text().strip()
            email = self.input_email.text().strip()
            senha = self.input_senha.text()
            ok, msg = validar_nome(nome)
            if not ok:
                return False
            ok, msg = validar_email(email)
            if not ok:
                return False
            ok, msg = validar_senha(senha)
            return ok
        else:
            senha = self.input_senha.text()
            ok, msg = validar_senha(senha)
            if not ok:
                return False
            if self._single_user:
                return True
            ident = self.input_email.text().strip()
            if not ident:
                return False
            if "@" in ident:
                ok, msg = validar_email(ident)
                return ok
            ok, msg = validar_nome(ident)
            return ok

    def handle_enter_from(self, widget):
        """
        Navegação por Enter: pular para o próximo campo; se próximo for o botão e
        todos os campos estiverem válidos, acionar.
        """
        ordered = []
        if self.modo_cadastro:
            if self.input_nome.isVisible():
                ordered.append(self.input_nome)
            if self.input_email.isVisible():
                ordered.append(self.input_email)
            ordered.append(self.input_senha)
        else:
            if self._single_user:
                ordered.append(self.input_senha)
            else:
                if self.input_email.isVisible():
                    ordered.append(self.input_email)
                ordered.append(self.input_senha)

        ordered.append(self.botao_principal)

        try:
            idx = ordered.index(widget)
        except ValueError:
            self.focusNextChild()
            return

        next_idx = idx + 1
        if next_idx < len(ordered):
            next_widget = ordered[next_idx]
            if isinstance(next_widget, QPushButton):
                if self._inputs_filled_for_current_mode():
                    try:
                        next_widget.click()
                    except Exception:
                        try:
                            self.executar_acao()
                        except Exception:
                            pass
                else:
                    next_widget.setFocus()
            else:
                next_widget.setFocus()
        else:
            if self._inputs_filled_for_current_mode():
                try:
                    self.botao_principal.click()
                except Exception:
                    try:
                        self.executar_acao()
                    except Exception:
                        pass
            else:
                self.focusNextChild()

    def _attempt_auth(self, identifier: str, senha: str) -> Tuple[bool, object]:
        identifier = (identifier or "").strip()
        senha = (senha or "")

        try:
            sucesso, resultado = autenticar(identifier, senha)
            if sucesso:
                return True, resultado
        except Exception:
            pass

        if identifier and "@" not in identifier:
            user = buscar_usuario_por_nome(identifier)
            if user:
                try:
                    sucesso, resultado = autenticar(user.get('email'), senha)
                    if sucesso:
                        return True, resultado
                except Exception:
                    pass

        if identifier:
            user = buscar_usuario_por_email(identifier)
            if user:
                try:
                    sucesso, resultado = autenticar(user.get('email'), senha)
                    if sucesso:
                        return True, resultado
                except Exception:
                    pass

        return False, "Email/nome ou senha inválidos."

    def executar_acao(self):
        email_or_identifier = self.input_email.text().strip()
        senha = self.input_senha.text()

        if self.modo_cadastro:
            nome = self.input_nome.text().strip()
            email = self.input_email.text().strip()

            ok, msg = validar_nome(nome)
            if not ok:
                QMessageBox.warning(self, "Erro", msg)
                self.input_nome.setFocus()
                return
            ok, msg = validar_email(email)
            if not ok:
                QMessageBox.warning(self, "Erro", msg)
                self.input_email.setFocus()
                return
            ok, msg = validar_senha(senha)
            if not ok:
                QMessageBox.warning(self, "Erro", msg)
                self.input_senha.setFocus()
                return

            try:
                sucesso, mensagem = criar_usuario(nome, email, senha)
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao criar usuário: {e}")
                return

            if sucesso:
                QMessageBox.information(self, "Sucesso", mensagem)
                self.alternar_modo()
                QTimer.singleShot(50, self._check_single_user)
            else:
                QMessageBox.warning(self, "Erro", mensagem)
        else:
            if self._single_user and (not email_or_identifier):
                email_or_identifier = self._single_user.get('email') or self._single_user.get('nome')

            ok, msg = validar_senha(senha)
            if not ok:
                QMessageBox.warning(self, "Erro", msg)
                self.input_senha.setFocus()
                return

            if email_or_identifier:
                if "@" in email_or_identifier:
                    ok, msg = validar_email(email_or_identifier)
                    if not ok:
                        QMessageBox.warning(self, "Erro", msg)
                        self.input_email.setFocus()
                        return
                else:
                    ok, msg = validar_nome(email_or_identifier)
                    if not ok:
                        QMessageBox.warning(self, "Erro", msg)
                        self.input_email.setFocus()
                        return
            else:
                if not self._single_user:
                    QMessageBox.warning(self, "Erro", "Email ou nome é necessário.")
                    self.input_email.setFocus()
                    return

            sucesso, resultado = self._attempt_auth(email_or_identifier, senha)
            if sucesso:
                try:
                    QMessageBox.information(self, "Bem-vindo", f"Olá, {resultado.get('nome', 'Usuário')}!")
                except Exception:
                    QMessageBox.information(self, "Bem-vindo", "Login efetuado!")
                try:
                    self.ao_logar_callback(resultado)
                except Exception:
                    pass
            else:
                QMessageBox.warning(self, "Erro", resultado)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Se estivermos no fallback, crie um usuário de exemplo para facilitar testes locais.
    if _use_fallback:
        try:
            # evita duplicação
            if not listar_usuarios():
                base_criar_usuario("DevUser", "dev@example.com", "1234")
        except Exception:
            pass

    login = TelaLogin(lambda user: print(f"Logou: {user}"))
    login.show()
    sys.exit(app.exec_())
 