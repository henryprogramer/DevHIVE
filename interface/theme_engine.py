from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

from banco.controles.tema.controle_tema import ControleTema


@dataclass
class ThemeTokens:
    mode: str
    scope: str
    bg: str
    fg: str
    main_bg: str
    header_bg: str
    nav_bg: str
    surface_bg: str
    input_bg: str
    border_color: str
    accent: str
    image_path: Optional[str] = None
    image_opacity: float = 0.8


def load_active_theme_record() -> Optional[Dict[str, Any]]:
    try:
        controller = ControleTema()
        try:
            return controller.get_active()
        finally:
            controller.close()
    except Exception:
        return None


def _safe_color(value: Optional[str], fallback: str) -> str:
    if not value:
        return fallback
    q = QColor(value)
    if not q.isValid():
        return fallback
    return q.name()


def _is_dark(color_value: str) -> bool:
    q = QColor(color_value)
    if not q.isValid():
        return False
    luminance = (0.299 * q.red()) + (0.587 * q.green()) + (0.114 * q.blue())
    return luminance < 145


def _contrast_text(color_value: str) -> str:
    return "#f4f7fb" if _is_dark(color_value) else "#121722"


def _rgba(color_value: str, alpha_float: float) -> str:
    q = QColor(color_value)
    if not q.isValid():
        q = QColor("#000000")
    alpha = max(0.0, min(1.0, alpha_float))
    return f"rgba({q.red()}, {q.green()}, {q.blue()}, {alpha:.3f})"


def build_theme_tokens(theme: Optional[Dict[str, Any]] = None, scope_override: Optional[str] = None) -> ThemeTokens:
    theme = theme or {}
    mode = str(theme.get("theme_mode") or "dark").lower()
    if mode not in {"dark", "light"}:
        mode = "dark"

    scope = scope_override or str(theme.get("scope") or "Global")
    if scope not in {"Global", "Navbar", "Header", "Main"}:
        scope = "Global"

    defaults = {
        "dark": {
            "bg": "#0f141b",
            "fg": "#f3f7ff",
            "main_bg": "#151c25",
            "header_bg": "#0f141b",
            "nav_bg": "#111821",
            "surface_bg": "#1b2532",
            "input_bg": "#121a24",
            "border": "#2c3f55",
            "accent": "#33a2ff",
        },
        "light": {
            "bg": "#eef3f9",
            "fg": "#131925",
            "main_bg": "#ffffff",
            "header_bg": "#e7edf5",
            "nav_bg": "#ecf1f8",
            "surface_bg": "#ffffff",
            "input_bg": "#ffffff",
            "border": "#b7c7da",
            "accent": "#1769ff",
        },
    }[mode]

    custom_bg = _safe_color(theme.get("cor_fundo"), "")
    accent = _safe_color(theme.get("cor_destaque"), defaults["accent"])

    bg = defaults["bg"]
    fg = defaults["fg"]
    main_bg = defaults["main_bg"]
    header_bg = defaults["header_bg"]
    nav_bg = defaults["nav_bg"]

    if custom_bg:
        if scope == "Global":
            bg = custom_bg
            main_bg = custom_bg
            header_bg = custom_bg
            nav_bg = custom_bg
            fg = _contrast_text(custom_bg)
        elif scope == "Navbar":
            nav_bg = custom_bg
        elif scope == "Header":
            header_bg = custom_bg
        elif scope == "Main":
            main_bg = custom_bg

    surface_bg = defaults["surface_bg"] if scope != "Global" else _rgba(fg, 0.08 if mode == "dark" else 0.04)
    input_bg = defaults["input_bg"] if scope != "Global" else _rgba(bg, 0.18 if mode == "dark" else 0.72)
    border_color = defaults["border"] if scope != "Global" else _rgba(fg, 0.22 if mode == "dark" else 0.25)

    image_path = theme.get("imagem_fundo")
    if image_path:
        image_path = str(image_path)
        if not Path(image_path).exists():
            image_path = None
    else:
        image_path = None

    try:
        image_opacity = float(theme.get("imagem_opacity") or 0.8)
    except Exception:
        image_opacity = 0.8

    return ThemeTokens(
        mode=mode,
        scope=scope,
        bg=bg,
        fg=fg,
        main_bg=main_bg,
        header_bg=header_bg,
        nav_bg=nav_bg,
        surface_bg=surface_bg,
        input_bg=input_bg,
        border_color=border_color,
        accent=accent,
        image_path=image_path,
        image_opacity=max(0.0, min(1.0, image_opacity)),
    )


def build_main_qss(tokens: ThemeTokens) -> str:
    hover_bg = _rgba(tokens.accent, 0.14 if tokens.mode == "dark" else 0.10)
    pressed_bg = _rgba(tokens.accent, 0.22 if tokens.mode == "dark" else 0.16)
    border = tokens.border_color
    selection_fg = _contrast_text(tokens.accent)

    qss = f"""
* {{
    color: {tokens.fg};
    selection-background-color: {tokens.accent};
    selection-color: {selection_fg};
}}

QWidget#centralWidget {{
    background-color: {tokens.bg};
}}

QFrame#header {{
    background-color: {tokens.header_bg};
    border: 1px solid {border};
    border-radius: 10px;
}}

QFrame#navbar, QWidget#navContent {{
    background-color: {tokens.nav_bg};
}}

QFrame#navbar {{
    border: 1px solid {border};
    border-radius: 10px;
}}

QFrame#main {{
    background-color: {tokens.main_bg};
    border: 1px solid {border};
    border-radius: 10px;
}}

QFrame#painel_customizacao, QFrame#profileFrame, QFrame#profileCard,
QFrame#metricCard, QFrame#kanbanBoardCard, QFrame#kanbanColumn,
QFrame#kanbanCard, QFrame#chatBubble, QFrame#agentStatusCard {{
    background-color: {tokens.surface_bg};
    border: 1px solid {border};
    border-radius: 10px;
}}

QLabel#titulo {{
    font-size: 18px;
    font-weight: 700;
}}

QLabel#mainHeader {{
    font-size: 16px;
    font-weight: 600;
}}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget {{
    background-color: {tokens.input_bg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px;
}}

QPushButton {{
    background-color: transparent;
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px 10px;
}}

QPushButton:hover {{
    background-color: {hover_bg};
}}

QPushButton:pressed {{
    background-color: {pressed_bg};
}}

QPushButton#winClose {{
    border-color: {_rgba("#c23934", 0.65)};
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QFrame#kanbanBoardCard:hover {{
    border: 1px solid {tokens.accent};
}}

QPushButton#btnAbrirQuadro {{
    font-weight: bold;
}}
"""

    if tokens.image_path:
        url = QUrl.fromLocalFile(str(Path(tokens.image_path).resolve())).toString()
        scope_selector = {
            "Global": "QWidget#centralWidget",
            "Navbar": "QFrame#navbar",
            "Header": "QFrame#header",
            "Main": "QFrame#main",
        }.get(tokens.scope, "QWidget#centralWidget")
        qss += f"""
{scope_selector} {{
    border-image: url("{url}") 0 0 0 0 stretch stretch;
}}
"""
    return qss


def build_login_qss(tokens: ThemeTokens) -> str:
    dark = tokens.mode == "dark"
    container_bg = _rgba("#000000", 0.80) if dark else _rgba("#ffffff", 0.90)
    container_border = _rgba(tokens.accent, 0.60)
    input_line = _rgba(tokens.fg, 0.26)
    logo_bg = _rgba("#ffffff", 0.14) if dark else _rgba("#111111", 0.08)
    logo_border = _rgba(tokens.fg, 0.12)
    primary_hover_bg = _rgba(tokens.accent, 1.0)
    primary_hover_fg = _contrast_text(tokens.accent)

    qss = f"""
QWidget#loginRoot {{
    background-color: transparent;
    color: {tokens.fg};
}}

QFrame#container {{
    background-color: {container_bg};
    border-radius: 30px;
    border: 2px solid {container_border};
}}

QLabel#logoLabel, QLabel#splashLogo {{
    background-color: {logo_bg};
    border: 1px solid {logo_border};
    border-radius: 14px;
    padding: 8px;
}}

QLineEdit#input {{
    background: transparent;
    border: none;
    border-bottom: 1px solid {input_line};
    padding: 0px 15px;
    font-size: 16px;
    min-height: 55px;
}}

QLineEdit#input:focus {{
    border-bottom: 1px solid {tokens.accent};
}}

QFrame#passwordFrame QLineEdit#input {{
    border: none;
    min-height: 40px;
}}

QFrame#passwordFrame {{
    background: transparent;
    border: none;
    border-bottom: 1px solid {input_line};
}}

QFrame#passwordFrame:hover {{
    border-bottom: 1px solid {tokens.accent};
}}

QPushButton#botaoPrincipal {{
    background-color: transparent;
    border: 2px solid {tokens.accent};
    border-radius: 25px;
    padding: 14px;
    font-weight: bold;
    font-size: 16px;
}}

QPushButton#botaoPrincipal:hover {{
    background-color: {primary_hover_bg};
    color: {primary_hover_fg};
}}

QPushButton#botaoLink {{
    background: transparent;
    border: none;
    font-size: 14px;
}}

QPushButton#botaoLink:hover {{
    text-decoration: underline;
}}

QPushButton#windowBtn {{
    background: transparent;
    border: none;
    font-weight: bold;
    font-size: 18px;
}}

QPushButton#windowBtn:hover {{
    color: {tokens.accent};
}}

QPushButton#eyeBtn {{
    background: transparent;
    border: none;
}}

QLabel#fotoThumb {{
    border-radius: 8px;
    background: {_rgba(tokens.fg, 0.08 if dark else 0.05)};
    border: 1px solid {_rgba(tokens.fg, 0.16)};
}}
"""
    if tokens.image_path:
        url = QUrl.fromLocalFile(str(Path(tokens.image_path).resolve())).toString()
        qss += f"""
QWidget#loginRoot {{
    border-image: url("{url}") 0 0 0 0 stretch stretch;
}}
"""
    return qss


def apply_palette(app: QApplication, tokens: ThemeTokens) -> None:
    pal = app.palette()
    bg_q = QColor(tokens.bg)
    fg_q = QColor(tokens.fg)
    base_q = QColor(tokens.main_bg)
    accent_q = QColor(tokens.accent)
    pal.setColor(QPalette.Window, bg_q)
    pal.setColor(QPalette.WindowText, fg_q)
    pal.setColor(QPalette.Base, base_q)
    pal.setColor(QPalette.AlternateBase, QColor(tokens.surface_bg))
    pal.setColor(QPalette.Text, fg_q)
    pal.setColor(QPalette.Button, base_q)
    pal.setColor(QPalette.ButtonText, fg_q)
    pal.setColor(QPalette.Highlight, accent_q)
    pal.setColor(QPalette.HighlightedText, QColor(_contrast_text(tokens.accent)))
    try:
        placeholder = QColor(fg_q)
        placeholder.setAlpha(145)
        pal.setColor(QPalette.PlaceholderText, placeholder)
    except Exception:
        pass
    app.setPalette(pal)
