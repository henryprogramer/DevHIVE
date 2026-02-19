from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ContextoComando:
    texto_original: str
    session_id: Optional[int] = None
    usuario: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

