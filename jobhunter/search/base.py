"""Contratos base para fontes de pesquisa de vagas.

Cada fonte concreta implementa `search()` usando apenas canais que permitem
acesso automatizado (APIs publicas/oficiais) ou paginas publicas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class SearchFilters:
    query: str = ""
    country: str = ""
    state: str = ""
    city: str = ""
    neighborhood: str = ""
    work_mode: str = ""          # Presencial/Híbrido/Remoto
    contract_type: str = ""      # CLT/Estágio/...
    area: str = ""
    days: Optional[int] = 7      # None => sem limite
    custom_since: Optional[datetime] = None

    def since_date(self) -> Optional[datetime]:
        if self.custom_since:
            return self.custom_since
        if self.days:
            return datetime.now() - timedelta(days=self.days)
        return None


@dataclass
class JobResult:
    title: str
    url: str
    source: str
    company_name: str = ""
    description: str = ""
    location: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    work_mode: str = ""
    contract_type: str = ""
    area: str = ""
    salary: str = ""
    source_id: str = ""
    published_at: str = ""       # ISO ou texto; usado para filtro de periodo
    is_remote: bool = False


class JobSource:
    """Interface de uma fonte de vagas."""

    name: str = "base"
    requires_key: bool = False
    key_setting: str = ""
    description: str = ""

    def is_available(self) -> bool:
        return True

    def search(self, filters: SearchFilters, max_results: int = 100) -> list[JobResult]:
        raise NotImplementedError


def parse_date(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    value = value.strip()
    fmts = [
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(value[: len(fmt) + 6].strip(), fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def within_period(value: str | None, filters: SearchFilters) -> bool:
    since = filters.since_date()
    if since is None:
        return True
    parsed = parse_date(value)
    if parsed is None:
        return True  # nao descartar vagas sem data confiavel
    return parsed >= since
