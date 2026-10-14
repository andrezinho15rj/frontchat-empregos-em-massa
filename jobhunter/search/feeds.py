"""Fontes de vagas SEM chave de API (APIs públicas gratuitas e feeds/RSS).

Todas as fontes deste módulo funcionam sem qualquer configuração de chave.
Requisitos: conexão com a internet. Nenhuma delas pede cadastro/API key.

Inclui:
- Jobicy, Working Nomads, Remote OK, Himalayas (endpoints públicos em JSON)
- We Work Remotely (raspagem do feed RSS público)
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

from ..logging_setup import get_logger
from .base import JobResult, JobSource, SearchFilters, within_period

log = get_logger("search.feeds")

USER_AGENT = "FrontchatEmpregosEmMassa/1.0 (+https://github.com/andrezinho15rj)"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", text)).strip()


def _matches(query: str, *fields: str) -> bool:
    if not query:
        return True
    q = query.lower()
    return any(q in (f or "").lower() for f in fields)


def _epoch_to_iso(value) -> str:
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return str(value or "")


class JobicySource(JobSource):
    name = "Jobicy"
    description = "Jobicy — vagas remotas (endpoint público JSON, sem chave)."

    API = "https://jobicy.com/api/v2/remote-jobs"

    def search(self, filters: SearchFilters, max_results: int = 100) -> list[JobResult]:
        try:
            resp = requests.get(self.API, params={"count": min(max_results, 50)}, timeout=30,
                                headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # pragma: no cover - rede externa
            log.warning("Jobicy indisponível: %s", exc)
            return []

        results: list[JobResult] = []
        for job in data.get("jobs", []) or []:
            title = job.get("jobTitle", "")
            desc = _strip_html(job.get("jobDescription") or job.get("jobExcerpt") or "")
            if not _matches(filters.query, title, desc, job.get("companyName", "")):
                continue
            pub = job.get("pubDate", "")
            if not within_period(pub, filters):
                continue
            geo = job.get("jobGeo", "") or ""
            salary = ""
            if job.get("salaryMin") or job.get("salaryMax"):
                salary = f"{job.get('salaryMin', '')}-{job.get('salaryMax', '')} {job.get('salaryCurrency', '')}".strip()
            results.append(JobResult(
                title=title.strip(),
                url=job.get("url", "").strip(),
                source=self.name,
                company_name=job.get("companyName", "").strip(),
                description=desc[:5000],
                location=geo,
                work_mode="Remoto",
                contract_type=", ".join(job.get("jobType", []) or []),
                area=", ".join(job.get("jobIndustry", []) or [])[:120],
                salary=salary,
                source_id=str(job.get("id", "")),
                published_at=pub,
                is_remote=True,
            ))
            if len(results) >= max_results:
                break
        log.info("Jobicy: %d vagas", len(results))
        return results


class WorkingNomadsSource(JobSource):
    name = "Working Nomads"
    description = "Working Nomads — vagas remotas (endpoint público JSON, sem chave)."

    API = "https://www.workingnomads.com/api/exposed_jobs/"

    def search(self, filters: SearchFilters, max_results: int = 100) -> list[JobResult]:
        try:
            resp = requests.get(self.API, timeout=30, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # pragma: no cover
            log.warning("Working Nomads indisponível: %s", exc)
            return []

        results: list[JobResult] = []
        for job in data or []:
            title = job.get("title", "")
            desc = _strip_html(job.get("description", ""))
            if not _matches(filters.query, title, desc, job.get("company_name", "")):
                continue
            pub = job.get("pub_date", "")
            if not within_period(pub, filters):
                continue
            results.append(JobResult(
                title=title.strip(),
                url=job.get("url", "").strip(),
                source=self.name,
                company_name=(job.get("company_name") or "").strip(),
                description=desc[:5000],
                location=job.get("location", "") or "Global",
                work_mode="Remoto",
                contract_type="Remoto",
                area=job.get("category_name", "") or "",
                salary="",
                source_id=job.get("url", ""),
                published_at=pub,
                is_remote=True,
            ))
            if len(results) >= max_results:
                break
        log.info("Working Nomads: %d vagas", len(results))
        return results


class RemoteOKSource(JobSource):
    name = "Remote OK"
    description = "Remote OK — vagas remotas (endpoint público JSON, sem chave)."

    API = "https://remoteok.com/api"

    def search(self, filters: SearchFilters, max_results: int = 100) -> list[JobResult]:
        try:
            resp = requests.get(self.API, timeout=30, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # pragma: no cover
            log.warning("Remote OK indisponível: %s", exc)
            return []

        results: list[JobResult] = []
        for job in data or []:
            if not isinstance(job, dict) or "position" not in job:
                continue  # primeiro item costuma ser aviso legal
            title = job.get("position", "")
            desc = _strip_html(job.get("description", ""))
            if not _matches(filters.query, title, desc, job.get("company", "")):
                continue
            pub = _epoch_to_iso(job.get("epoch") or job.get("date"))
            if not within_period(pub, filters):
                continue
            location = job.get("location", "") or "Remoto"
            results.append(JobResult(
                title=title.strip(),
                url=job.get("url", "").strip(),
                source=self.name,
                company_name=(job.get("company") or "").strip(),
                description=desc[:5000],
                location=location,
                city=location,
                work_mode="Remoto",
                contract_type="Remoto",
                area=", ".join(job.get("tags", []) or [])[:120],
                salary="",
                source_id=str(job.get("id", "")),
                published_at=pub,
                is_remote=True,
            ))
            if len(results) >= max_results:
                break
        log.info("Remote OK: %d vagas", len(results))
        return results


class HimalayasSource(JobSource):
    name = "Himalayas"
    description = "Himalayas — vagas remotas (endpoint público JSON, sem chave)."

    API = "https://himalayas.app/jobs/api"

    def search(self, filters: SearchFilters, max_results: int = 100) -> list[JobResult]:
        try:
            resp = requests.get(self.API, params={"limit": min(max_results, 50)}, timeout=30,
                                headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # pragma: no cover
            log.warning("Himalayas indisponível: %s", exc)
            return []

        results: list[JobResult] = []
        for job in data.get("jobs", []) or []:
            title = job.get("title", "")
            desc = _strip_html(job.get("description") or job.get("excerpt") or "")
            if not _matches(filters.query, title, desc, job.get("companyName", "")):
                continue
            pub = _epoch_to_iso(job.get("pubDate"))
            if not within_period(pub, filters):
                continue
            url = job.get("applicationLink") or job.get("guid") or ""
            locs = job.get("locationRestrictions", []) or []
            salary = ""
            if job.get("minSalary") or job.get("maxSalary"):
                salary = f"{job.get('minSalary', '')}-{job.get('maxSalary', '')} {job.get('currency', '')}".strip()
            results.append(JobResult(
                title=title.strip(),
                url=url.strip(),
                source=self.name,
                company_name=(job.get("companyName") or "").strip(),
                description=desc[:5000],
                location=", ".join(locs)[:200] or "Remoto",
                work_mode="Remoto",
                contract_type=job.get("employmentType", "") or "Remoto",
                area=", ".join(job.get("categories", []) or [])[:120],
                salary=salary,
                source_id=str(job.get("guid", "")),
                published_at=pub,
                is_remote=True,
            ))
            if len(results) >= max_results:
                break
        log.info("Himalayas: %d vagas", len(results))
        return results


class WeWorkRemotelySource(JobSource):
    name = "We Work Remotely"
    description = "We Work Remotely — raspagem do feed RSS público (sem chave)."

    RSS = "https://weworkremotely.com/remote-jobs.rss"

    def search(self, filters: SearchFilters, max_results: int = 100) -> list[JobResult]:
        try:
            resp = requests.get(self.RSS, timeout=30, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as exc:  # pragma: no cover
            log.warning("We Work Remotely indisponível: %s", exc)
            return []

        results: list[JobResult] = []
        for item in root.findall(".//item"):
            def _txt(tag: str) -> str:
                el = item.find(tag)
                return (el.text or "").strip() if el is not None and el.text else ""

            raw_title = _txt("title")
            company, _, role = raw_title.partition(":")
            role = role.strip() or raw_title.strip()
            desc = _strip_html(_txt("description"))
            if not _matches(filters.query, role, raw_title, desc, company):
                continue
            pub = _txt("pubDate")
            if not within_period(pub, filters):
                continue
            country = _txt("country") or _txt("region")
            results.append(JobResult(
                title=role,
                url=_txt("link"),
                source=self.name,
                company_name=company.strip(),
                description=desc[:5000],
                location=country or "Remoto",
                city=_txt("state"),
                work_mode="Remoto",
                contract_type=_txt("type") or "Remoto",
                area=_txt("category")[:120],
                salary="",
                source_id=_txt("guid"),
                published_at=pub,
                is_remote=True,
            ))
            if len(results) >= max_results:
                break
        log.info("We Work Remotely: %d vagas", len(results))
        return results
