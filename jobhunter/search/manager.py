"""Orquestrador de busca de vagas.

Executa todas as fontes disponiveis, normaliza, deduplica e persiste no banco.
Nunca cria dados falsos: se nenhuma fonte retornar resultados, retorna vazio.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..db.repositories import company_repo, job_repo
from ..logging_setup import get_logger
from .arbeitnow import ArbeitnowSource
from .base import JobResult, JobSource, SearchFilters
from .feeds import (
    HimalayasSource, JobicySource, RemoteOKSource, WeWorkRemotelySource,
    WorkingNomadsSource,
)
from .remotive import RemotiveSource

log = get_logger("search.manager")

# Todas as fontes funcionam SEM chave de API (apenas internet).
ALL_SOURCES: list[JobSource] = [
    RemotiveSource(),
    ArbeitnowSource(),
    JobicySource(),
    RemoteOKSource(),
    HimalayasSource(),
    WorkingNomadsSource(),
    WeWorkRemotelySource(),
]


@dataclass
class SearchReport:
    total_found: int = 0
    total_saved: int = 0
    per_source: dict[str, int] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


def _domain_from_url(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url or "")
    if not m:
        return ""
    host = m.group(1).lower()
    return host[4:] if host.startswith("www.") else host


def _infer_area(title: str) -> str:
    tl = (title or "").lower()
    mapping = {
        "Administrativo": ["administrativ", "auxiliar admin", "assistente admin", "secretár"],
        "Comercial / Vendas": ["vend", "comercial", "consultor de vend", "representante"],
        "Tecnologia": ["desenvolvedor", "programador", "dev ", "analista de sistemas",
                       "suporte técnico", "ti ", "qa ", "dados", "engenheiro de software"],
        "Atendimento / SAC": ["atendimento", "sac", "telemarketing", "recepção"],
        "Logística": ["logística", "logistica", "estoque", "expedição", "motorista", "entregador"],
        "Financeiro": ["financeir", "contab", "fiscal", "tesouraria", "analista financeiro"],
        "Marketing": ["marketing", "social media", "growth", "seo"],
        "Recursos Humanos": ["recursos humanos", " rh ", "recrutamento", "seleção"],
    }
    for area, kws in mapping.items():
        if any(k in tl for k in kws):
            return area
    return ""


def _source_by_name(name: str) -> JobSource | None:
    for s in ALL_SOURCES:
        if s.name == name:
            return s
    return None


class SearchManager:
    def list_sources(self) -> list[JobSource]:
        return list(ALL_SOURCES)

    def search(self, filters: SearchFilters, source_names: list[str] | None = None,
               max_per_source: int = 100, on_progress=None) -> SearchReport:
        report = SearchReport()
        sources = ALL_SOURCES
        if source_names:
            sources = [s for s in ALL_SOURCES if s.name in source_names]

        for src in sources:
            if on_progress:
                on_progress(f"Pesquisando em {src.name}...")
            if not src.is_available():
                report.errors[src.name] = "Fonte indisponível no momento."
                report.per_source[src.name] = 0
                continue
            try:
                jobs = src.search(filters, max_results=max_per_source)
            except Exception as exc:  # pragma: no cover - rede externa
                log.exception("Falha na fonte %s", src.name)
                report.errors[src.name] = str(exc)
                report.per_source[src.name] = 0
                continue
            report.per_source[src.name] = len(jobs)
            report.total_found += len(jobs)
            report.total_saved += self._persist(jobs)

        log.info("Busca concluída: encontrados=%d salvos=%d",
                 report.total_found, report.total_saved)
        return report

    def _persist(self, jobs: list[JobResult]) -> int:
        saved = 0
        seen_urls: set[str] = set()
        for job in jobs:
            if not job.url or job.url in seen_urls:
                continue
            seen_urls.add(job.url)
            company_id = None
            if job.company_name:
                domain = _domain_from_url(job.url)
                company_id = company_repo.get_or_create(
                    job.company_name, domain=domain or None, location=job.location)
            area = job.area or _infer_area(job.title)
            jid = job_repo.upsert({
                "company_id": company_id,
                "title": job.title,
                "description": job.description,
                "location": job.location,
                "city": job.city, "state": job.state, "country": job.country,
                "work_mode": job.work_mode, "contract_type": job.contract_type,
                "area": area, "salary": job.salary, "url": job.url,
                "source": job.source, "source_id": job.source_id,
                "published_at": job.published_at, "is_remote": job.is_remote,
            })
            if jid:
                saved += 1
        return saved


search_manager = SearchManager()
