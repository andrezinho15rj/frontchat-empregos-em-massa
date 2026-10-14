"""Testes de banco: persistência, reabertura sem perda e deduplicação."""
from __future__ import annotations

import unittest

from .base import DBTestCase


class DatabaseTests(DBTestCase):
    def test_insert_and_persist_across_reconnect(self):
        from jobhunter.db.repositories import company_repo, job_repo
        from jobhunter.db.database import database

        cid = company_repo.get_or_create("Empresa Teste", domain="empresa.com.br")
        job_repo.upsert({
            "company_id": cid, "title": "Analista Administrativo",
            "url": "https://empresa.com.br/vagas/1", "source": "Teste",
            "published_at": "2026-01-01",
        })
        self.assertEqual(job_repo.count(), 1)

        # fecha e reabre -> dados persistem
        database.close()
        database.path = self.path
        self.assertEqual(job_repo.count(), 1)
        self.assertEqual(company_repo.list()[0]["name"], "Empresa Teste")

    def test_job_url_dedup(self):
        from jobhunter.db.repositories import job_repo
        for _ in range(3):
            job_repo.upsert({"title": "Dev", "url": "https://x.com/1", "source": "T"})
        self.assertEqual(job_repo.count(), 1)

    def test_wipe_all(self):
        from jobhunter.db.repositories import company_repo, job_repo
        from jobhunter.db.database import database
        cid = company_repo.get_or_create("A")
        job_repo.upsert({"company_id": cid, "title": "B", "url": "https://a.com/1"})
        database.wipe_all()
        self.assertEqual(job_repo.count(), 0)


if __name__ == "__main__":
    unittest.main()
