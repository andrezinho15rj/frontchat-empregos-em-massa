"""Importacao e extracao de texto de curriculos (PDF e DOCX)."""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import app_paths
from ..logging_setup import get_logger

log = get_logger("resume.parser")


class ResumeImportError(Exception):
    pass


def _extract_pdf(path: Path) -> str:
    try:
        import pdfplumber
    except Exception as exc:  # pragma: no cover
        raise ResumeImportError("Biblioteca pdfplumber não instalada.") from exc
    chunks = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks).strip()


def _extract_docx(path: Path) -> str:
    try:
        import docx  # python-docx
    except Exception as exc:  # pragma: no cover
        raise ResumeImportError("Biblioteca python-docx não instalada.") from exc
    doc = docx.Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n".join(parts).strip()


def extract_text(src_path: str | Path) -> tuple[str, str]:
    """Extrai o texto do curriculo. Retorna (texto, tipo)."""
    path = Path(src_path)
    if not path.exists():
        raise ResumeImportError(f"Arquivo não encontrado: {path}")
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path), "pdf"
    if suffix in (".docx", ".doc"):
        return _extract_docx(path), "docx"
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore").strip(), "txt"
    raise ResumeImportError("Formato não suportado. Use PDF, DOCX ou TXT.")


def import_resume(src_path: str | Path, name: str | None = None) -> tuple[int, str, str]:
    """Copia o arquivo para a pasta de dados, extrai o texto e salva no banco.

    Retorna (resume_id, texto_extraido, tipo).
    """
    from ..db.repositories import resume_repo

    path = Path(src_path)
    text, ftype = extract_text(path)
    dest = app_paths.resumes_dir() / path.name
    if path.resolve() != dest.resolve():
        shutil.copy2(path, dest)
    rid = resume_repo.add(
        name=name or path.stem,
        file_path=str(dest),
        file_type=ftype,
        content_text=text,
        is_active=1,
    )
    resume_repo.set_active(rid)
    log.info("Currículo importado: %s (%s, %d chars)", dest.name, ftype, len(text))
    return rid, text, ftype


def candidate_name(text: str) -> str:
    """Tenta extrair o nome do candidato da primeira linha nao vazia."""
    for line in (text or "").splitlines():
        line = line.strip()
        if 2 < len(line) < 60 and not any(c.isdigit() for c in line):
            # evita capturar cabecalhos comuns
            low = line.lower()
            if any(w in low for w in ["curriculo", "currículo", "curriculum",
                                      "objetivo", "experiência", "experiencia",
                                      "resumo", "dados", "telefone", "e-mail", "email"]):
                continue
            return line
    return "Candidato(a)"
