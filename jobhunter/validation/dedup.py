"""Deduplicacao de contatos no banco."""
from __future__ import annotations

from ..constants import EmailStatus
from ..db.repositories import contact_repo
from ..logging_setup import get_logger

log = get_logger("validation.dedup")


def mark_duplicates() -> int:
    """Marca contatos cujo e-mail ja apareceu antes (mantém o mais antigo).

    Retorna quantos registros foram marcados como duplicados.
    """
    from ..db.database import database
    rows = database.query(
        "SELECT id, email FROM contacts WHERE email IS NOT NULL ORDER BY id ASC"
    )
    seen: dict[str, int] = {}
    marked = 0
    for r in rows:
        email = (r["email"] or "").lower()
        if email in seen:
            contact_repo.update(r["id"], is_duplicate=1,
                                status=EmailStatus.DUPLICATE.value)
            marked += 1
        else:
            seen[email] = r["id"]
            # garante que o primeiro nao carregue flag antiga
            database.execute("UPDATE contacts SET is_duplicate=0 WHERE id=?", (r["id"],))
    log.info("Deduplicação: %d duplicados marcados", marked)
    return marked


def is_duplicate_email(email: str, exclude_id: int | None = None) -> bool:
    from ..db.database import database
    row = database.query_one(
        "SELECT id FROM contacts WHERE email=? AND id<>?",
        ((email or "").lower(), exclude_id or -1),
    )
    return bool(row)
