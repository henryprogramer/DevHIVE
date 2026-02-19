from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Optional

from nucleo.comandos.contexto import ContextoComando


CommandHandler = Callable[[ContextoComando, str], str]


@dataclass
class ComandoDef:
    keyword: str
    description: str
    handler: CommandHandler
    aliases: Iterable[str] = field(default_factory=tuple)


@dataclass
class ResultadoComando:
    matched: bool
    keyword: Optional[str] = None
    message: Optional[str] = None


class RegistroComandos:
    def __init__(self):
        self._handlers: Dict[str, ComandoDef] = {}

    def register(
        self,
        keyword: str,
        handler: CommandHandler,
        description: str = "",
        aliases: Iterable[str] = (),
    ) -> None:
        normalized = keyword.strip().lower()
        if not normalized:
            raise ValueError("keyword inválida")
        cmd = ComandoDef(
            keyword=normalized,
            description=description.strip(),
            handler=handler,
            aliases=tuple(a.strip().lower() for a in aliases if a.strip()),
        )
        self._handlers[normalized] = cmd
        for alias in cmd.aliases:
            self._handlers[alias] = cmd

    def list_commands(self) -> Dict[str, str]:
        unique = {}
        for cmd in self._handlers.values():
            unique[cmd.keyword] = cmd.description
        return dict(sorted(unique.items()))

    def dispatch(self, texto: str, contexto: ContextoComando) -> ResultadoComando:
        raw = (texto or "").strip()
        if not raw:
            return ResultadoComando(matched=False)

        token, sep, remainder = raw.partition(" ")
        if token.startswith(("/", "!")):
            keyword = token[1:].strip().lower()
        else:
            keyword = token.strip().lower()
        keyword = keyword.rstrip(":")

        cmd = self._handlers.get(keyword)
        if not cmd:
            return ResultadoComando(matched=False)

        args = remainder.strip() if sep else ""
        try:
            output = cmd.handler(contexto, args)
        except Exception as exc:
            output = f"Comando '{cmd.keyword}' reconhecido, mas falhou ao executar: {exc}"
        return ResultadoComando(matched=True, keyword=cmd.keyword, message=output)
