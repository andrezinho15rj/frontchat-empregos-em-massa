"""Repositorios: acesso a dados organizado por entidade."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ..constants import EmailStatus
from .database import database


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SettingsRepo:
    def get(self, key: str, default: str | None = None) -> str | None:
        row = database.query_one("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        database.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self.get(key)
        if val is None:
            return default
        return val.lower() in ("1", "true", "sim", "yes")

    def all(self) -> dict[str, str]:
        return {r["key"]: r["value"] for r in database.query("SELECT key, value FROM settings")}


class CompanyRepo:
    def get_or_create(self, name: str, domain: str | None = None, **fields) -> int:
        name = (name or "").strip()
        domain = (domain or "").strip().lower() or None
        row = None
        if domain:
            row = database.query_one(
                "SELECT id FROM companies WHERE name=? AND domain=?", (name, domain)
            )
        if not row:
            row = database.query_one(
                "SELECT id FROM companies WHERE name=? AND (domain IS NULL OR domain='')", (name,)
            )
        if row:
            cid = row["id"]
            updates = {k: v for k, v in fields.items() if v}
            if updates:
                sets = ", ".join(f"{k}=?" for k in updates)
                database.execute(
                    f"UPDATE companies SET {sets}, updated_at=? WHERE id=?",
                    (*updates.values(), _now(), cid),
                )
            return cid

        cur = database.execute(
            "INSERT INTO companies(name, domain, website, careers_url, location, notes) "
            "VALUES(?,?,?,?,?,?)",
            (
                name, domain, fields.get("website"), fields.get("careers_url"),
                fields.get("location"), fields.get("notes"),
            ),
        )
        return cur.lastrowid

    def get(self, cid: int):
        return database.query_one("SELECT * FROM companies WHERE id=?", (cid,))

    def by_domain(self, domain: str):
        return database.query_one(
            "SELECT * FROM companies WHERE domain=? ORDER BY id LIMIT 1", (domain.lower(),)
        )

    def list(self, search: str = "", limit: int = 1000):
        if search:
            like = f"%{search}%"
            return database.query(
                "SELECT * FROM companies WHERE name LIKE ? OR domain LIKE ? OR location LIKE ? "
                "ORDER BY updated_at DESC LIMIT ?",
                (like, like, like, limit),
            )
        return database.query("SELECT * FROM companies ORDER BY updated_at DESC LIMIT ?", (limit,))

    def update(self, cid: int, **fields) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        database.execute(
            f"UPDATE companies SET {sets}, updated_at=? WHERE id=?",
            (*fields.values(), _now(), cid),
        )


class JobRepo:
    def upsert(self, job: dict[str, Any]) -> Optional[int]:
        """Insere ou atualiza uma vaga pela URL (chave natural). Retorna o id."""
        url = (job.get("url") or "").strip()
        if not url:
            return None
        existing = database.query_one("SELECT id FROM jobs WHERE url=?", (url,))
        if existing:
            return existing["id"]
        cur = database.execute(
            """INSERT INTO jobs(company_id, title, description, location, city, state,
                country, work_mode, contract_type, area, salary, url, source, source_id,
                published_at, is_remote)
               VALUES(:company_id, :title, :description, :location, :city, :state,
                :country, :work_mode, :contract_type, :area, :salary, :url, :source,
                :source_id, :published_at, :is_remote)""",
            {
                "company_id": job.get("company_id"),
                "title": job.get("title") or "",
                "description": job.get("description") or "",
                "location": job.get("location") or "",
                "city": job.get("city") or "",
                "state": job.get("state") or "",
                "country": job.get("country") or "",
                "work_mode": job.get("work_mode") or "",
                "contract_type": job.get("contract_type") or "",
                "area": job.get("area") or "",
                "salary": job.get("salary") or "",
                "url": url,
                "source": job.get("source") or "",
                "source_id": job.get("source_id") or "",
                "published_at": job.get("published_at") or "",
                "is_remote": 1 if job.get("is_remote") else 0,
            },
        )
        return cur.lastrowid

    def list(self, search: str = "", area: str = "", source: str = "",
             only_with_company: bool = False, limit: int = 5000):
        clauses, params = [], []
        if search:
            like = f"%{search}%"
            clauses.append("(j.title LIKE ? OR j.location LIKE ? OR c.name LIKE ?)")
            params += [like, like, like]
        if area:
            clauses.append("j.area=?")
            params.append(area)
        if source:
            clauses.append("j.source=?")
            params.append(source)
        if only_with_company:
            clauses.append("j.company_id IS NOT NULL")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        return database.query(
            f"""SELECT j.*, c.name AS company_name, c.domain AS company_domain,
                   c.website AS company_website
                FROM jobs j LEFT JOIN companies c ON c.id=j.company_id
                {where} ORDER BY j.id DESC LIMIT ?""",
            tuple(params),
        )

    def get(self, jid: int):
        return database.query_one(
            """SELECT j.*, c.name AS company_name, c.domain AS company_domain
               FROM jobs j LEFT JOIN companies c ON c.id=j.company_id WHERE j.id=?""",
            (jid,),
        )

    def link_company(self, jid: int, company_id: int) -> None:
        database.execute("UPDATE jobs SET company_id=? WHERE id=?", (company_id, jid))

    def count(self) -> int:
        return database.query_one("SELECT COUNT(*) AS n FROM jobs")["n"]


class ContactRepo:
    def add(self, company_id: int, email: str | None = None, form_url: str | None = None,
            domain: str | None = None, source_url: str | None = None,
            category: str = "", status: str = EmailStatus.UNCHECKED.value,
            job_id: int | None = None) -> Optional[int]:
        email_norm = (email or "").strip().lower() or None
        # dedup natural: mesmo email na mesma empresa
        if email_norm:
            existing = database.query_one(
                "SELECT id FROM contacts WHERE email=? AND company_id=?",
                (email_norm, company_id),
            )
            if existing:
                return existing["id"]
        cur = database.execute(
            """INSERT INTO contacts(company_id, job_id, email, form_url, domain,
                source_url, category, status, found_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (company_id, job_id, email_norm, form_url, domain, source_url,
             category, status, _now()),
        )
        return cur.lastrowid

    def update(self, cid: int, **fields) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        database.execute(f"UPDATE contacts SET {sets} WHERE id=?", (*fields.values(), cid))

    def get(self, cid: int):
        return database.query_one(
            """SELECT ct.*, c.name AS company_name, c.website AS company_website
               FROM contacts ct LEFT JOIN companies c ON c.id=ct.company_id
               WHERE ct.id=?""", (cid,),
        )

    def list(self, search: str = "", status: str = "", only_candidates: bool = False,
             limit: int = 5000):
        clauses, params = [], []
        if search:
            like = f"%{search}%"
            clauses.append("(ct.email LIKE ? OR c.name LIKE ? OR ct.domain LIKE ?)")
            params += [like, like, like]
        if status:
            clauses.append("ct.status=?")
            params.append(status)
        if only_candidates:
            clauses.append("ct.email IS NOT NULL AND ct.is_duplicate=0 "
                           "AND ct.status IN (?,?)")
            params += [EmailStatus.FOUND_CONFIRMED.value, EmailStatus.DOMAIN_VALID.value]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        return database.query(
            f"""SELECT ct.*, c.name AS company_name FROM contacts ct
                LEFT JOIN companies c ON c.id=ct.company_id
                {where} ORDER BY ct.id DESC LIMIT ?""",
            tuple(params),
        )

    def all_emails_lower(self) -> set[str]:
        return {r["email"].lower() for r in
                database.query("SELECT email FROM contacts WHERE email IS NOT NULL")}

    def count(self, status: str | None = None) -> int:
        if status:
            return database.query_one(
                "SELECT COUNT(*) AS n FROM contacts WHERE status=?", (status,))["n"]
        return database.query_one("SELECT COUNT(*) AS n FROM contacts")["n"]


class ResumeRepo:
    def add(self, name: str, file_path: str, file_type: str, content_text: str,
            is_active: int = 1) -> int:
        cur = database.execute(
            "INSERT INTO resumes(name, file_path, file_type, content_text, is_active) "
            "VALUES(?,?,?,?,?)",
            (name, file_path, file_type, content_text, is_active),
        )
        return cur.lastrowid

    def set_active(self, rid: int) -> None:
        database.execute("UPDATE resumes SET is_active=0")
        database.execute("UPDATE resumes SET is_active=1 WHERE id=?", (rid,))

    def active(self):
        return database.query_one(
            "SELECT * FROM resumes WHERE is_active=1 ORDER BY id DESC LIMIT 1")

    def list(self):
        return database.query("SELECT * FROM resumes ORDER BY id DESC")

    def get(self, rid: int):
        return database.query_one("SELECT * FROM resumes WHERE id=?", (rid,))


class CampaignRepo:
    def create(self, name: str, resume_id: int | None, subject_tpl: str, body_tpl: str,
               language: str = "pt") -> int:
        cur = database.execute(
            "INSERT INTO campaigns(name, resume_id, subject_tpl, body_tpl, status, language) "
            "VALUES(?,?,?,?,?,?)",
            (name, resume_id, subject_tpl, body_tpl, "Aguardando revisão", language),
        )
        return cur.lastrowid

    def update(self, cid: int, **fields) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        database.execute(
            f"UPDATE campaigns SET {sets}, updated_at=? WHERE id=?",
            (*fields.values(), _now(), cid),
        )

    def get(self, cid: int):
        return database.query_one("SELECT * FROM campaigns WHERE id=?", (cid,))

    def list(self):
        return database.query("SELECT * FROM campaigns ORDER BY id DESC")


class ApplicationRepo:
    def add(self, **fields) -> Optional[int]:
        try:
            cur = database.execute(
                """INSERT INTO applications(campaign_id, company_id, job_id, contact_id,
                    to_email, subject, body, resume_id, status, match_score, match_reason)
                   VALUES(:campaign_id, :company_id, :job_id, :contact_id, :to_email,
                    :subject, :body, :resume_id, :status, :match_score, :match_reason)""",
                {
                    "campaign_id": fields.get("campaign_id"),
                    "company_id": fields.get("company_id"),
                    "job_id": fields.get("job_id"),
                    "contact_id": fields.get("contact_id"),
                    "to_email": fields.get("to_email"),
                    "subject": fields.get("subject"),
                    "body": fields.get("body"),
                    "resume_id": fields.get("resume_id"),
                    "status": fields.get("status") or "Preparada",
                    "match_score": fields.get("match_score"),
                    "match_reason": fields.get("match_reason"),
                },
            )
            return cur.lastrowid
        except Exception:
            return None

    def update(self, aid: int, **fields) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k}=?" for k in fields)
        database.execute(
            f"UPDATE applications SET {sets}, updated_at=? WHERE id=?",
            (*fields.values(), _now(), aid),
        )

    def get(self, aid: int):
        return database.query_one(
            """SELECT a.*, c.name AS company_name, j.title AS job_title
               FROM applications a
               LEFT JOIN companies c ON c.id=a.company_id
               LEFT JOIN jobs j ON j.id=a.job_id WHERE a.id=?""", (aid,),
        )

    def list(self, campaign_id: int | None = None, status: str = "", search: str = "",
             limit: int = 5000):
        clauses, params = [], []
        if campaign_id:
            clauses.append("a.campaign_id=?")
            params.append(campaign_id)
        if status:
            clauses.append("a.status=?")
            params.append(status)
        if search:
            like = f"%{search}%"
            clauses.append("(a.to_email LIKE ? OR c.name LIKE ? OR a.subject LIKE ?)")
            params += [like, like, like]
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        return database.query(
            f"""SELECT a.*, c.name AS company_name, j.title AS job_title
                FROM applications a
                LEFT JOIN companies c ON c.id=a.company_id
                LEFT JOIN jobs j ON j.id=a.job_id
                {where} ORDER BY a.id DESC LIMIT ?""", tuple(params),
        )

    def already_applied(self, company_id: int, job_id: int | None, email: str) -> bool:
        return bool(database.query_one(
            "SELECT id FROM applications WHERE company_id=? AND IFNULL(job_id,0)=IFNULL(?,0) "
            "AND to_email=? AND status='Enviada'",
            (company_id, job_id, (email or "").lower()),
        ))

    def count(self, status: str | None = None) -> int:
        if status:
            return database.query_one(
                "SELECT COUNT(*) AS n FROM applications WHERE status=?", (status,))["n"]
        return database.query_one("SELECT COUNT(*) AS n FROM applications")["n"]


settings_repo = SettingsRepo()
company_repo = CompanyRepo()
job_repo = JobRepo()
contact_repo = ContactRepo()
resume_repo = ResumeRepo()
campaign_repo = CampaignRepo()
application_repo = ApplicationRepo()
