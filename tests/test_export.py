"""Testes de exportação CSV/XLSX."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from .base import DBTestCase


class ExportTests(DBTestCase):
    def _seed(self):
        from jobhunter.db.repositories import company_repo, contact_repo, job_repo
        cid = company_repo.get_or_create("Empresa Export", domain="exp.com.br")
        jid = job_repo.upsert({
            "company_id": cid, "title": "Analista", "url": "https://exp.com.br/v/1",
            "source": "Teste", "city": "São Paulo", "state": "SP",
            "published_at": "2026-01-10", "area": "Administrativo",
        })
        contact_repo.add(cid, email="rh@exp.com.br", domain="exp.com.br",
                         source_url="https://exp.com.br/contatos", job_id=jid)
        return cid, jid

    def test_csv_export(self):
        from jobhunter.export import exporter
        self._seed()
        rows = exporter.preview()
        self.assertTrue(any(r["email"] == "rh@exp.com.br" for r in rows))
        out = Path(tempfile.mkdtemp()) / "out.csv"
        exporter.to_csv(rows, out)
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8-sig")
        self.assertIn("rh@exp.com.br", content)

    def test_xlsx_export(self):
        from jobhunter.export import exporter
        self._seed()
        rows = exporter.preview()
        out = Path(tempfile.mkdtemp()) / "out.xlsx"
        exporter.to_xlsx(rows, out)
        self.assertTrue(out.exists() and out.stat().st_size > 1000)
        from openpyxl import load_workbook
        wb = load_workbook(out)
        values = [c.value for c in wb.active[2]]
        self.assertIn("rh@exp.com.br", values)


if __name__ == "__main__":
    unittest.main()
