"""Definicao do schema SQLite.

O banco e criado automaticamente no primeiro uso. Todas as migracoes sao
idempotentes (CREATE TABLE IF NOT EXISTS / ADD COLUMN tolerante).
"""
from __future__ import annotations

SCHEMA_VERSION = 1

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    domain       TEXT,
    website      TEXT,
    careers_url  TEXT,
    location     TEXT,
    notes        TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, domain)
);
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);

CREATE TABLE IF NOT EXISTS jobs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id     INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    title          TEXT NOT NULL,
    description    TEXT,
    location       TEXT,
    city           TEXT,
    state          TEXT,
    country        TEXT,
    work_mode      TEXT,
    contract_type  TEXT,
    area           TEXT,
    salary         TEXT,
    url            TEXT NOT NULL,
    source         TEXT NOT NULL,
    source_id      TEXT,
    published_at   TEXT,
    is_remote      INTEGER DEFAULT 0,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(url)
);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_published ON jobs(published_at);

CREATE TABLE IF NOT EXISTS contacts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id     INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    job_id         INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    email          TEXT,
    form_url       TEXT,
    domain         TEXT,
    source_url     TEXT,
    category       TEXT,
    status         TEXT NOT NULL DEFAULT 'Não verificado',
    mx_ok          INTEGER DEFAULT 0,
    syntax_ok      INTEGER DEFAULT 0,
    is_duplicate   INTEGER DEFAULT 0,
    notes          TEXT,
    found_at       TEXT NOT NULL DEFAULT (datetime('now')),
    checked_at     TEXT,
    UNIQUE(email, company_id)
);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);

CREATE TABLE IF NOT EXISTS resumes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    file_path     TEXT NOT NULL,
    file_type     TEXT,
    content_text  TEXT,
    is_active     INTEGER DEFAULT 1,
    imported_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS campaigns (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    resume_id      INTEGER REFERENCES resumes(id) ON DELETE SET NULL,
    subject_tpl    TEXT,
    body_tpl       TEXT,
    status         TEXT NOT NULL DEFAULT 'Rascunho',
    language       TEXT DEFAULT 'pt',
    provider       TEXT,
    from_email     TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id    INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    company_id     INTEGER REFERENCES companies(id) ON DELETE SET NULL,
    job_id         INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    contact_id     INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
    to_email       TEXT,
    subject        TEXT,
    body           TEXT,
    resume_id      INTEGER REFERENCES resumes(id) ON DELETE SET NULL,
    status         TEXT NOT NULL DEFAULT 'Preparada',
    error          TEXT,
    match_score    REAL,
    match_reason   TEXT,
    prepared_at    TEXT NOT NULL DEFAULT (datetime('now')),
    sent_at        TEXT,
    updated_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(campaign_id, company_id, job_id, to_email)
);
CREATE INDEX IF NOT EXISTS idx_apps_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_apps_campaign ON applications(campaign_id);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS event_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    level      TEXT,
    module     TEXT,
    message    TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""
