"""Consulta de registros MX de dominio (dnspython).

A presenca de MX indica que o dominio pode receber e-mail — NAO confirma que
uma caixa postal especifica existe. Isso e tratado explicitamente no módulo de
validacao.
"""
from __future__ import annotations

from functools import lru_cache

from ..logging_setup import get_logger

log = get_logger("validation.mx")

try:
    import dns.resolver  # type: ignore
    _DNS_AVAILABLE = True
except Exception:  # pragma: no cover
    _DNS_AVAILABLE = False


PUBLIC_DNS = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]


def _resolve_with(domain: str, nameservers: list[str] | None, timeout: float) -> bool:
    resolver = dns.resolver.Resolver(configure=nameservers is None)
    if nameservers is not None:
        resolver.nameservers = nameservers
    resolver.timeout = timeout
    resolver.lifetime = timeout
    for rtype in ("MX", "A"):
        try:
            answers = resolver.resolve(domain, rtype)
            if len(answers) > 0:
                return True
        except Exception:
            continue
    return False


@lru_cache(maxsize=2048)
def has_mx(domain: str, timeout: float = 6.0) -> bool:
    if not domain:
        return False
    if not _DNS_AVAILABLE:
        log.warning("dnspython indisponível — MX não verificado para %s", domain)
        return False
    # 1) resolver do sistema
    try:
        if _resolve_with(domain, None, timeout):
            return True
    except Exception:
        pass
    # 2) fallback para resolvers públicos (quando o DNS local está indisponível)
    for ns in PUBLIC_DNS:
        try:
            if _resolve_with(domain, [ns], timeout):
                return True
        except Exception:
            continue
    return False


def dns_available() -> bool:
    return _DNS_AVAILABLE
