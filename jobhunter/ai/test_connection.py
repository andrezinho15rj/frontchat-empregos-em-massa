"""Teste de conexao com o provedor de IA configurado."""
from __future__ import annotations

from ..logging_setup import get_logger
from .client import AIClient, AIUnavailableError

log = get_logger("ai")


def test_connection() -> tuple[bool, str]:
    client = AIClient()
    if not client.is_available():
        return False, "IA não configurada (verifique base URL, modelo e chave)."
    try:
        text = client.complete_text("Responda em uma palavra.",
                                    "Diga apenas: OK", max_tokens=5)
        return True, f"Conexão OK. Resposta do modelo: {text.strip()[:60]}"
    except AIUnavailableError as exc:
        return False, str(exc)
    except Exception as exc:  # pragma: no cover
        return False, f"Falha de conexão: {exc}"
