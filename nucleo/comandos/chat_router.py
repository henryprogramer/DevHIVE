from typing import Optional

from nucleo.comandos.contexto import ContextoComando
from nucleo.comandos.registro import RegistroComandos, ResultadoComando

_REGISTRY: Optional[RegistroComandos] = None


def _placeholder(domain: str):
    def _handler(ctx: ContextoComando, args: str) -> str:
        args_msg = f" Args: {args}" if args else ""
        return (
            f"Comando '{domain}' reconhecido.{args_msg}\n"
            "Infraestrutura pronta: você pode ligar este comando aos controladores reais agora."
        )

    return _handler


def _help_handler(ctx: ContextoComando, args: str) -> str:
    registry = get_registry()
    lines = ["Comandos-base disponíveis:"]
    for key, description in registry.list_commands().items():
        desc = description or "sem descrição"
        lines.append(f"- {key}: {desc}")
    lines.append("Use '/comando argumentos' ou 'comando argumentos'.")
    return "\n".join(lines)


def get_registry() -> RegistroComandos:
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY

    reg = RegistroComandos()
    reg.register("ajuda", _help_handler, "Lista os comandos cadastrados", aliases=("help", "comandos"))
    reg.register("kanban", _placeholder("kanban"), "Ponto de entrada para automações de quadro/coluna/card")
    reg.register("arquivos", _placeholder("arquivos"), "Ponto de entrada para operações de pasta/arquivo")
    reg.register("tema", _placeholder("tema"), "Ponto de entrada para criar/aplicar temas")
    reg.register("biblioteca", _placeholder("biblioteca"), "Ponto de entrada para consultas de armazenamento")
    reg.register("sistema", _placeholder("sistema"), "Ponto de entrada para ações gerais da interface")
    _REGISTRY = reg
    return reg


def dispatch_chat_command(texto: str, session_id: Optional[int] = None, usuario: Optional[str] = None) -> ResultadoComando:
    contexto = ContextoComando(texto_original=texto, session_id=session_id, usuario=usuario)
    registry = get_registry()
    return registry.dispatch(texto, contexto)

