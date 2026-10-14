"""Fonte: Remotive (API publica oficial, sem chave).

https://remotive.com/api/remote-jobs
"""
from __future__ import annotations

import re

import requests

from ..logging_setup import get_logger
from .base import JobResult, JobSource, SearchFilters, within_period

log = get_logger("search.remotive")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class RemotiveSource(JobSource):
    name = "Remotive"
    description = "API pública Remotive — vagas remotas internacionais."

    API = "https://remotive.com/api/remote-jobs"

    def is_available(self) -> bool:
        return True

    def search(self, filters: SearchFilters, max_results: int = 100) -> list[JobResult]:
        params = {"limit": min(max_results, 200)}
        if filters.query:
            params["search"] = filters.query
        try:
            resp = requests.get(self.API, params=params, timeout=30,
                                headers={"User-Agent": "FrontchatEmpregosEmMassa/1.0"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # pragma: no cover - rede externa
            log.warning("Remotive indisponível: %s", exc)
            return []

        results: list[JobResult] = []
        for job in data.get("jobs", []):
            pub = job.get("publication_date", "")
            if not within_period(pub, filters):
                continue
            location = job.get("candidate_required_location", "")
            if filters.country and filters.country.lower() not in location.lower():
                if "worldwide" not in location.lower() and "anywhere" not in location.lower():
                    continue
            results.append(JobResult(
                title=job.get("title", "").strip(),
                url=job.get("url", "").strip(),
                source=self.name,
                company_name=job.get("company_name", "").strip(),
                description=_strip_html(job.get("description", ""))[:5000],
                location=location,
                work_mode="Remoto" if job.get("candidate_required_location") else "Remoto",
                contract_type="Remoto",
                area=job.get("category", ""),
                salary=job.get("salary", ""),
                source_id=str(job.get("id", "")),
                published_at=pub,
                is_remote=True,
            ))
            if len(results) >= max_results:
                break
        log.info("Remotive: %d vagas", len(results))
        return results
