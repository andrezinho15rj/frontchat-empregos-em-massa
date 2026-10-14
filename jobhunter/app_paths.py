"""Resolucao de caminhos de dados do aplicativo.

Todos os dados persistentes ficam em
%LOCALAPPDATA%\\FrontchatEmpregosEmMassa, de forma que a aplicacao funcione no
Windows mesmo apos empacotamento com PyInstaller (onde o diretorio do
executavel e somente leitura/temporario).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "FrontchatEmpregosEmMassa"


def is_frozen() -> bool:
    """True quando rodando a partir do executavel gerado pelo PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def _base_local_appdata() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local)
    # Fallback para ambientes nao-Windows (desenvolvimento/testes)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    return Path.home() / ".local" / "share"


def data_dir() -> Path:
    """Diretorio raiz de dados persistentes (criado se nao existir)."""
    override = os.environ.get("JOBHUNTER_DATA_DIR")
    base = Path(override) if override else _base_local_appdata() / APP_DIR_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def db_path() -> Path:
    return data_dir() / "jobhunter.db"


def resumes_dir() -> Path:
    d = data_dir() / "curriculos"
    d.mkdir(parents=True, exist_ok=True)
    return d


def logs_dir() -> Path:
    d = data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def exports_dir() -> Path:
    d = data_dir() / "exportacoes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def attachments_dir() -> Path:
    d = data_dir() / "anexos_campanha"
    d.mkdir(parents=True, exist_ok=True)
    return d


def resource_path(relative: str) -> Path:
    """Resolve um recurso empacotado (icones etc) tanto em dev quanto no EXE."""
    if is_frozen():
        root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        root = Path(__file__).resolve().parent.parent
    return root / relative
