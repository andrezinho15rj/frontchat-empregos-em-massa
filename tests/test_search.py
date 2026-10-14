"""Testes de integração da busca real de vagas (requer internet).

Executados apenas quando a rede está disponível. Usam apenas fontes públicas que
NÃO exigem chave de API.
"""
from __future__ import annotations

import unittest

from jobhunter.search import ALL_SOURCES, SearchFilters, search_manager
from jobhunter.search.remotive import RemotiveSource

from .base import DBTestCase, network_available


class KeylessSourceTests(unittest.TestCase):
    def test_nenhuma_fonte_exige_chave(self):
        self.assertTrue(ALL_SOURCES)
        for src in ALL_SOURCES:
            self.assertFalse(src.requires_key, f"{src.name} exige chave")
            self.assertTrue(src.is_available(), f"{src.name} indisponível")


@unittest.skipUnless(network_available(), "rede indisponível")
class SearchIntegrationTests(DBTestCase):
    def test_remotive_returns_real_jobs(self):
        src = RemotiveSource()
        self.assertTrue(src.is_available())
        jobs = src.search(SearchFilters(query="support", days=30), max_results=5)
        # Pode retornar 0 dependendo do momento; validamos a estrutura
        for job in jobs:
            self.assertTrue(job.url.startswith("http"))
            self.assertTrue(job.title)
            self.assertEqual(job.source, "Remotive")

    def test_manager_persists_jobs(self):
        report = search_manager.search(SearchFilters(query="developer", days=30),
                                       source_names=["Remotive"], max_per_source=5)
        self.assertGreaterEqual(report.total_found, 0)
        from jobhunter.db.repositories import job_repo
        self.assertEqual(job_repo.count(), report.total_saved)


if __name__ == "__main__":
    unittest.main()
