"""Armazenamento seguro de credenciais no Windows.

Usa o Windows Credential Manager via biblioteca `keyring` quando disponivel.
Nunca grava senhas/tokens em texto puro no banco de dados ou em arquivos.
"""
from __future__ import annotations

from ..logging_setup import get_logger

log = get_logger("security")

SERVICE = "FrontchatEmpregosEmMassa"

try:
    import keyring  # type: ignore
    _KEYRING = True
except Exception:  # pragma: no cover
    _KEYRING = False


def available() -> bool:
    return _KEYRING


def set_secret(name: str, value: str) -> None:
    if _KEYRING:
        try:
            keyring.set_password(SERVICE, name, value)
            return
        except Exception as exc:  # pragma: no cover
            log.warning("keyring indisponível para '%s': %s", name, exc)
    log.warning("keyring indisponível — segredo '%s' não foi persistido.", name)


def get_secret(name: str) -> str:
    if _KEYRING:
        try:
            return keyring.get_password(SERVICE, name) or ""
        except Exception:  # pragma: no cover
            return ""
    return ""


def delete_secret(name: str) -> None:
    if _KEYRING:
        try:
            keyring.delete_password(SERVICE, name)
        except Exception:
            pass
