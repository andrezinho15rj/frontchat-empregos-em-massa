"""Fonte: Arbeitnow (API publica oficial, sem chave).

https://www.arbeitnow.com/api/job-board-api
Paginação via ?page=N
"""
from __future__ import annotations

import re

import requests

from ..logging_setup import get_logger
from .base import JobResult, JobSource, SearchFilters, within_period

log = get_logger("search.arbeitnow")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class ArbeitnowSource(JobSource):
    name = "Arbeitnow"
    description = "API pública Arbeitnow — vagas (foco Europa/remoto)."

    API = "https://www.arbeitnow.com/api/job-board-api"

    def search(self, filters: SearchFilters, max_results: int = 100) -> list[JobResult]:
        results: list[JobResult] = []
        query = (filters.query or "").lower()
        page = 1
        max_pages = 8
        try:
            while len(results) < max_results and page <= max_pages:
                resp = requests.get(self.API, params={"page": page}, timeout=30,
                                    headers={"User-Agent": "FrontchatEmpregosEmMassa/1.0"})
                resp.raise_for_status()
                data = resp.json().get("data", [])
                if not data:
                    break
                for job in data:
                    title = job.get("title", "")
                    desc = _strip_html(job.get("description", ""))
                    if query and query not in title.lower() and query not in desc.lower():
                        continue
                    if not within_period(_to_iso(job.get("created_at")), filters):
                        continue
                    location = job.get("location", "")
                    if filters.city and filters.city.lower() not in location.lower():
                        continue
                    results.append(JobResult(
                        title=title.strip(),
                        url=job.get("url", "").strip(),
                        source=self.name,
                        company_name=job.get("company_name", "").strip(),
                        description=desc[:5000],
                        location=location,
                        city=location,
                        work_mode="Remoto" if job.get("remote") else "",
                        contract_type=", ".join(job.get("job_types", []) or []),
                        area=", ".join(job.get("tags", []) or [])[:120],
                        source_id=job.get("slug", ""),
                        published_at=_to_iso(job.get("created_at")),
                        is_remote=bool(job.get("remote")),
                    ))
                    if len(results) >= max_results:
                        break
                page += 1
        except Exception as exc:  # pragma: no cover
            log.warning("Arbeitnow indisponível: %s", exc)
        log.info("Arbeitnow: %d vagas", len(results))
        return results


def _to_iso(ts) -> str:
    if not ts:
        return ""
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return str(ts)
