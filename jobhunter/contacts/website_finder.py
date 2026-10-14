"""Descoberta do site oficial da empresa.

Estrategia (sem inventar dominios e SEM chave de API):
1. Usa o dominio ja conhecido da empresa (extraido da URL da vaga).
2. Se ausente, tenta o dominio presente na propria URL da vaga.
Nunca construi dominios a partir do nome da empresa.
"""
from __future__ import annotations

import re

from ..logging_setup import get_logger

log = get_logger("contacts.website")

# Dominios de portais/agregadores que NAO sao o site da empresa
AGGREGATORS = [
    "linkedin.com", "glassdoor", "indeed", "gupy.io", "kenoby", "solides",
    "catho", "vagas.com", "infojobs", "trabalhabrasil", "empregos.com",
    "remotive.com", "arbeitnow.com", "adzuna", "jooble", "bne.com.br",
    "curriculum.com.br", "empregosagora", "jooble.org", "jobatus",
    "sine.com.br", "empregabrasil", "trabalheconosco",
]


def domain_from_url(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url or "")
    if not m:
        return ""
    host = m.group(1).lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def is_aggregator(domain: str) -> bool:
    d = (domain or "").lower()
    return any(a in d for a in AGGREGATORS)


def guess_site_from_job_url(job_url: str) -> str | None:
    domain = domain_from_url(job_url)
    if domain and not is_aggregator(domain):
        return f"https://{domain}"
    return None


def find_company_website(company_name: str, known_domain: str | None = None,
                         job_url: str | None = None) -> str | None:
    if known_domain and not is_aggregator(known_domain):
        return f"https://{known_domain}"
    if job_url:
        site = guess_site_from_job_url(job_url)
        if site:
            return site
    return None
