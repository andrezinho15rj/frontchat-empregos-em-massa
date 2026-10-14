"""Metricas reais do dashboard, calculadas a partir do banco."""
from __future__ import annotations

from .constants import ApplicationStatus, EmailStatus
from .db.database import database
from .db.repositories import application_repo, contact_repo


def dashboard_metrics() -> dict[str, int]:
    def n(sql, params=()):
        row = database.query_one(sql, params)
        return row["n"] if row else 0

    return {
        "empresas": n("SELECT COUNT(*) AS n FROM companies"),
        "vagas": n("SELECT COUNT(*) AS n FROM jobs"),
        "contatos": n("SELECT COUNT(*) AS n FROM contacts WHERE email IS NOT NULL"),
        "contatos_verificados": n(
            "SELECT COUNT(*) AS n FROM contacts WHERE status=?",
            (EmailStatus.FOUND_CONFIRMED.value,)),
        "contatos_dominio_ok": n(
            "SELECT COUNT(*) AS n FROM contacts WHERE status=?",
            (EmailStatus.DOMAIN_VALID.value,)),
        "candidaturas_preparadas": n(
            "SELECT COUNT(*) AS n FROM applications WHERE status=?",
            (ApplicationStatus.PREPARED.value,)),
        "emails_enviados": application_repo.count(ApplicationStatus.SENT.value),
        "envios_falha": application_repo.count(ApplicationStatus.FAILED.value),
        "respostas": application_repo.count(ApplicationStatus.REPLY.value),
        "entrevistas": application_repo.count(ApplicationStatus.INTERVIEW.value),
    }


def recent_activity(limit: int = 15):
    return database.query(
        """SELECT to_email, subject, status, sent_at, updated_at,
                  (SELECT name FROM companies WHERE id=applications.company_id) AS company
           FROM applications ORDER BY updated_at DESC LIMIT ?""", (limit,))
