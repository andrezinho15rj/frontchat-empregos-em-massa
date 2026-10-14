"""Base comum para os testes: banco isolado em diretório temporário."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Isola o diretório de dados ANTES de importar módulos do app
_TMP = tempfile.mkdtemp(prefix="jobhunter_tests_")
os.environ["JOBHUNTER_DATA_DIR"] = _TMP
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class DBTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from jobhunter.db.database import Database
        # sys.modules evita o shadowing de 'jobhunter.db.database' (instância x módulo)
        dbmod = sys.modules["jobhunter.db.database"]

        cls.path = Path(_TMP) / "test.db"
        test_db = Database(cls.path)
        test_db.initialize()
        dbmod.database.path = cls.path
        dbmod.database.close()

    def setUp(self):
        from jobhunter.db.database import database
        database.path = self.path
        database.close()
        database.initialize()
        # limpa tabelas entre testes
        for table in ["applications", "campaigns", "resumes", "contacts",
                      "jobs", "companies"]:
            database.execute(f"DELETE FROM {table}")


def network_available() -> bool:
    import socket
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=4).close()
        return True
    except Exception:
        return False
