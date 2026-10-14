"""Camada de conexao e inicializacao do banco SQLite."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from .. import app_paths
from ..logging_setup import get_logger
from . import schema

log = get_logger("db")

_local = threading.local()


class Database:
    """Gerenciador de conexao SQLite thread-local.

    Cada thread (incluindo workers de busca/validacao) recebe sua propria
    conexao, evitando o erro 'SQLite objects created in a thread...'.
    """

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else app_paths.db_path()
        self._lock = threading.Lock()

    def connect(self) -> sqlite3.Connection:
        conn = getattr(_local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.path), timeout=30, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA busy_timeout = 30000")
            _local.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(_local, "conn", None)
        if conn is not None:
            try:
                conn.close()
            finally:
                _local.conn = None

    def initialize(self) -> None:
        conn = self.connect()
        with self._lock:
            conn.executescript(schema.SCHEMA_SQL)
            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
                (str(schema.SCHEMA_VERSION),),
            )
            conn.commit()
        log.info("Banco de dados inicializado em %s", self.path)

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        conn = self.connect()
        cur = conn.execute(sql, params)
        conn.commit()
        return cur

    def query(self, sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
        return self.connect().execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple | dict = ()):
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def wipe_all(self) -> None:
        """Remove permanentemente todos os dados locais (LGPD)."""
        conn = self.connect()
        with self._lock:
            for table in [
                "applications", "campaigns", "resumes", "contacts",
                "jobs", "companies", "event_log", "settings",
            ]:
                conn.execute(f"DELETE FROM {table}")
            conn.commit()
        log.warning("Todos os dados locais foram apagados pelo usuario.")


# Instancia padrao compartilhada pelo aplicativo
database = Database()
